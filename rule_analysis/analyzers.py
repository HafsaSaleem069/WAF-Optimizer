import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import re
import json
import logging
import requests
from dotenv import load_dotenv
import os
import math
from collections import defaultdict
from random import randint

load_dotenv()

logger = logging.getLogger(__name__)


class GroqModelDeprecated(Exception):
    """Raised when the configured Groq model is decommissioned or unsupported"""
    pass

class GroqAIClient:
    """Centralized AI client for all WAF optimization tasks using Groq API"""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1"
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
            raise ValueError("Groq API key not configured")
        
        # Use only the model that we know works
        self.model = "llama-3.1-8b-instant"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Test API connection on initialization and expose availability flag
        self.available = self._test_api_connection()
    
    def _test_api_connection(self):
        """Test Groq API connection with a simple request"""
        try:
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Respond with just 'OK'"}],
                "max_tokens": 5,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                test_response = result['choices'][0]['message']['content'].strip()
                print(f"✅ Groq API connection test successful: '{test_response}'")
                return True
            else:
                print(f"❌ Groq API connection failed: {response.status_code} - {response.text}")
                raise Exception(f"Groq API connection failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Groq API connection error: {e}")
            raise Exception(f"Groq API connection error: {e}")
    
    def make_request(self, system_prompt, user_prompt, temperature=0.5, max_tokens=600):
        """Generic method for all AI requests using requests library (NO FUNCTION CALLING)"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # ... (rest of the API request logic remains the same) ...
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            # ... (rest of the error handling remains the same) ...
            
            result = response.json()
            
            # 💡 NOTE: The model's response structure changes. We now grab 'content'.
            return self._parse_text_response(result['choices'][0]['message']['content']) 
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_response = response.json()
                error_detail = f" - {error_response}"
            except Exception:
                error_detail = f" - Response: {response.text}"

            # Detect decommissioned model errors and expose a specific exception
            try:
                err_obj = response.json()
                if isinstance(err_obj, dict) and 'error' in err_obj:
                    code = None
                    msg = None
                    if isinstance(err_obj['error'], dict):
                        code = err_obj['error'].get('code')
                        msg = err_obj['error'].get('message')
                    else:
                        msg = str(err_obj['error'])
                    if code == 'model_decommissioned' or (isinstance(msg, str) and 'decommissioned' in msg.lower()):
                        # Mark client as unavailable to avoid further calls
                        self.available = False
                        logger.error(f"Groq model decommissioned: {msg}")
                        raise GroqModelDeprecated(msg)
            except Exception:
                # ignore parsing errors and continue to raise generic
                pass

            logger.error(f"Groq API HTTP error {response.status_code}: {e}{error_detail}")
            raise Exception(f"Groq API HTTP error {response.status_code}: {e}")
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise Exception(f"Groq API error: {e}")
    
    def optimize_redundant_rules(self, rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context):
        """Specific method for rule optimization with labeled text output"""
        
        system_prompt = """
        You are a WAF rule optimization expert. Your task is to analyze two rules and provide a single, prioritized suggestion to merge or remove one.
        
        **RESPOND WITH ONLY THE LABELED SECTIONS BELOW.** DO NOT add any extra explanation or introductory text.

        - **OPTIMIZED RULE SYNTAX:** [Provide the complete, single ModSecurity rule syntax here]
        - **ACTION:** [MERGE|REMOVE_RULE_A|REMOVE_RULE_B|KEEP_BOTH]
        - **EXPLANATION:** [Brief explanation of the decision.]
        - **SECURITY IMPACT:** [How security is maintained or improved.]
        - **PERFORMANCE IMPROVEMENT:** [Expected performance gain.]
        - **IMPLEMENTATION STEPS:** [Step 1; Step 2; Step 3; ...]
        """
        
        user_prompt = self._build_rule_optimization_prompt(
            rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context
        )
        
        # Use slightly higher temperature for better compliance
        return self.make_request(system_prompt, user_prompt, temperature=0.5, max_tokens=600)
    
    def _build_rule_optimization_prompt(self,
                                        rule_a_id, rule_b_id, relationship_type,
                                        rule_a_data, rule_b_data, analysis_context):

        # rule_a_data & rule_b_data are now dicts
        rule_a_details = {
            'attack_type': rule_a_data.get('attack_type', 'Unknown'),
            'severity': rule_a_data.get('severity', 'Unknown'),
            'matched_data': rule_a_data.get('matched_data', 'None'),
            'trigger_count': rule_a_data.get('trigger_count', 0)
        }
        rule_b_details = {
            'attack_type': rule_b_data.get('attack_type', 'Unknown'),
            'severity': rule_b_data.get('severity', 'Unknown'),
            'matched_data': rule_b_data.get('matched_data', 'None'),
            'trigger_count': rule_b_data.get('trigger_count', 0)
        }

        prompt = f"""
        Analyze these two WAF rules with a {relationship_type} relationship and suggest an optimized replacement:

        RULE A (ID: {rule_a_id}):
        - Attack Type: {rule_a_details['attack_type']}
        - Severity: {rule_a_details['severity']}
        - Matched Patterns: {rule_a_details['matched_data']}
        - Trigger Count: {rule_a_details['trigger_count']}

        RULE B (ID: {rule_b_id}):
        - Attack Type: {rule_b_details['attack_type']}
        - Severity: {rule_b_details['severity']}
        - Matched Patterns: {rule_b_details['matched_data']}
        - Trigger Count: {rule_b_details['trigger_count']}

        RELATIONSHIP: {relationship_type}
        CONFIDENCE: {analysis_context.get('confidence', 'N/A')}
        EVIDENCE COUNT: {analysis_context.get('evidence_count', 'N/A')}
        """
        return prompt
    
    def _extract_rule_details(self, rule_data):
        """Extract relevant details from rule data"""
        if rule_data.empty:
            return {
                'attack_type': 'Unknown',
                'severity': 'Unknown', 
                'matched_data': 'None',
                'trigger_count': 0
            }
        
        first_row = rule_data.iloc[0]
        return {
            'attack_type': first_row.get('attack_type', 'Unknown'),
            'severity': first_row.get('severity', 'Unknown'),
            'matched_data': first_row.get('matched_data', 'None'),
            'trigger_count': len(rule_data)
        }
    
    def _parse_text_response(self, ai_response):
        """
        Aggressively extracts the primary suggestion by identifying the main action 
        and the first complete pattern/JSON structure found in the raw text, 
        since the AI refuses to use markers.
        """
        raw_text = ai_response.strip()
        
        # 1. Initialize fallback result structure
        result = {
            "optimized_rule": "N/A (Pattern not found)",
            "action": "REVIEW_MANUALLY",
            "explanation": "AI output could not be parsed into structure. Requires manual review.",
            "security_impact": "Requires manual review.",
            "performance_improvement": "N/A",
            "implementation_steps": ["Check raw response for suggested actions."]
        }

        # 2. Extract potential JSON structures or SQL code blocks (Optionally provided by AI)
        # This targets the common JSON blocks the AI outputs.
        json_candidates = re.findall(r'\{.*?\}', raw_text, re.DOTALL)
        
        # 3. Analyze the overall text for the primary recommended action
        if re.search(r'Merge|combine', raw_text, re.IGNORECASE):
            result['action'] = "MERGE"
            result['explanation'] = "AI suggests merging the two rules."
        elif re.search(r'Remove Rule B|Remove Rule 1021|Remove Rule 1026|Remove Rule 1019|Remove Rule 1023', raw_text, re.IGNORECASE):
            result['action'] = "REMOVE_RULE_B"
            result['explanation'] = "AI suggests removing Rule B as redundant or lower priority."
        elif re.search(r'Downgrade|Modify Rule A|Update Rule 1001', raw_text, re.IGNORECASE):
            result['action'] = "MODIFY_RULE_A"
            result['explanation'] = "AI suggests modifying Rule A (often to merge pattern or change severity/action)."

        # 4. Extract the BEST PATTERN/RULE SYNTAX
        
        # A. Try to extract the pattern from the first JSON block, if present
        if json_candidates:
            # We try to clean and load the first candidate
            json_str = json_candidates[0]
            json_str = re.sub(r'//.*', '', json_str) # Remove comments
            try:
                parsed_json = json.loads(json_str)
                if 'pattern' in parsed_json:
                    pattern = parsed_json['pattern'].strip('"').strip()
                    result['optimized_rule'] = f"Suggested Pattern: {pattern}"
                    # If we get a rule ID, we can update the action if the JSON suggests it
                    if 'action' in parsed_json and 'severity' in parsed_json:
                        result['explanation'] += f" The AI provided a target JSON structure with action: {parsed_json['action']} and severity: {parsed_json['severity']}."
                elif 'rule_id' in parsed_json:
                    # If it's a valid JSON but no pattern, log what we got
                    result['optimized_rule'] = f"AI provided structural Rule Data, not final syntax."

            except json.JSONDecodeError:
                # Failed to parse the JSON block, so we move to text extraction
                pass 

        # B. If no pattern was extracted from JSON, try to extract from SQL code blocks
        if result['optimized_rule'] == "N/A (Pattern not found)":
            sql_match = re.search(r'```(?:sql)?\s*(.*?)\s*```', raw_text, re.DOTALL | re.IGNORECASE)
            if sql_match:
                pattern = sql_match.group(1).strip()
                result['optimized_rule'] = f"Suggested Pattern: {pattern}"
                result['explanation'] = "Rule pattern extracted from SQL code block."

        # 5. Final check for removal case
        if result['action'] == "REMOVE_RULE_B" and result['optimized_rule'] == "N/A (Pattern not found)":
            result['optimized_rule'] = "Keep Rule A as is, remove Rule B."


        # 6. We manually map the essential fields to fulfill the expected contract,
        # prioritizing the extracted 'action' and 'optimized_rule'.
        
        return {
            "optimized_rule": result['optimized_rule'],
            "action": result['action'],
            "explanation": result['explanation'],
            "security_impact": result['security_impact'],
            "performance_improvement": result['performance_improvement'],
            "implementation_steps": result['implementation_steps']
        }

class RuleAnalysisAIProcessor:
    """Processes rule relationship analysis results through Groq AI"""
    
    def __init__(self, rules_df: pd.DataFrame = None, ai_client=None):
        try:
            self.rules_df = rules_df
            self.ai_client = ai_client or GroqAIClient()
            self.ai_available = True
            print("✅ Groq AI client initialized successfully")
        except Exception as e:
            logger.warning(f"AI client initialization failed: {e}")
            self.ai_available = False
            self.ai_client = None
            print(f"❌ AI client initialization failed: {e}")

    def _get_rule_data(self, rule_id: str) -> Dict:
        """Extract data for a given rule_id from rules_df safely."""
        if self.rules_df is None or self.rules_df.empty:
            raise ValueError("rules_df is not available in RuleAnalysisAIProcessor")

        id_column = 'id' if 'id' in self.rules_df.columns else 'rule_id'
        rule_row = self.rules_df[self.rules_df[id_column].astype(str) == str(rule_id)]

        if rule_row.empty:
            logger.warning(f"No data found for rule {rule_id}")
            return {
                "rule_id": rule_id,
                "description": "N/A",
                "severity": "N/A",
                "action": "N/A",
                "phase": "N/A",
                "pattern": "N/A",
            }

        row = rule_row.iloc[0]
        return {
            "rule_id": str(rule_id),
            "description": row.get("msg", ""),
            "severity": row.get("severity", ""),
            "action": row.get("action", ""),
            "phase": row.get("phase", ""),
            "pattern": row.get("pattern", ""),
        }
    
    def enhance_analysis_with_ai(self, analysis_results: Dict, traffic_df: pd.DataFrame) -> Dict:
        """
        Use Groq AI to enhance rule relationship analysis results.
        - Sends redundant, shadowed, and correlated rule pairs to Groq for optimization insights.
        """

        if not self.ai_available or not self.ai_client:
            logger.warning("AI not available — returning base analysis only.")
            analysis_results["ai_available"] = False
            analysis_results["ai_error"] = "AI client not available"
            return analysis_results

        try:
            ai_suggestions = {
                "redundant": [],
                "shadowed": [],
                "correlated": []
            }

            # Loop over each relationship type
            for rel_type, rel_list in analysis_results.get("relationships", {}).items():
                for rel in rel_list:
                    rule_a_id = rel.get("rule_a")
                    rule_b_id = rel.get("rule_b")

                    if not rule_a_id or not rule_b_id:
                        continue

                    # Extract contextual rule data
                    rule_a_data = self._get_rule_data(rule_a_id)
                    rule_b_data = self._get_rule_data(rule_b_id)

                    # Prepare shared context
                    context = {
                        "relationship_type": rel_type,
                        "confidence": rel.get("confidence"),
                        "evidence_count": rel.get("evidence_count"),
                        "conflicting_fields": rel.get("conflicting_fields", {}),
                        "description": rel.get("description", "")
                    }

                    try:
                        # 🔹 Redundant Rules (merge/delete suggestions)
                        if rel_type == "RXD":
                            ai_response = self.ai_client.optimize_redundant_rules(
                                rule_a_id, rule_b_id, rel_type, rule_a_data, rule_b_data, context
                            )
                            ai_suggestions["redundant"].append(ai_response)

                        # 🔹 Shadowed Rules (identify dominant rule)
                        elif rel_type == "SHD":
                            user_prompt = (
                                f"Rule {rule_a_id} shadows {rule_b_id}. "
                                f"Suggest how to merge or remove one without reducing security.\n\n"
                                f"Rule A Data: {json.dumps(rule_a_data, indent=2, default=str)}\n"
                                f"Rule B Data: {json.dumps(rule_b_data, indent=2, default=str)}\n"
                            )
                            ai_response = self.ai_client.make_request(
                                "You are a WAF optimization expert. Suggest minimal-impact actions.",
                                user_prompt,
                                temperature=0.3,
                                max_tokens=800
                            )
                            ai_suggestions["shadowed"].append(ai_response)

                        # 🔹 Correlated Rules (suggest grouping or simplification)
                        elif rel_type == "COR":
                            user_prompt = (
                                f"Rules {rule_a_id} and {rule_b_id} often trigger together (correlated). "
                                f"Suggest optimization or grouping ideas.\n\n"
                                f"Rule A: {json.dumps(rule_a_data, indent=2, default=str)}\n"
                                f"Rule B: {json.dumps(rule_b_data, indent=2, default=str)}\n"
                                f"Traffic Context: {json.dumps(context, indent=2, default=str)}"
                            )
                            ai_response = self.ai_client.make_request(
                                "You are a ModSecurity correlation analyzer.",
                                user_prompt,
                                temperature=0.4,
                                max_tokens=800
                            )
                            ai_suggestions["correlated"].append(ai_response)
                            
                    except Exception as e:
                        logger.error(f"AI request failed for {rule_a_id} vs {rule_b_id}: {e}")
                        # Continue with other pairs instead of failing completely

            # Merge AI results into output
            analysis_results["ai_available"] = True
            analysis_results["ai_suggestions"] = ai_suggestions

            print(f"✅ AI enhancement completed successfully")
            return analysis_results

        except GroqModelDeprecated as e:
            # Specific handling when the configured Groq model is decommissioned
            logger.error(f"AI model decommissioned: {e}")
            analysis_results["ai_available"] = False
            analysis_results["ai_error"] = str(e)
            return analysis_results
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            analysis_results["ai_available"] = False
            analysis_results["ai_error"] = str(e)
            return analysis_results

# The RuleRelationshipAnalyzer class remains exactly the same as in your original code
class RuleRelationshipAnalyzer:
    def __init__(self, rules_df: pd.DataFrame, traffic_df: pd.DataFrame, enable_ai: bool = True,
                 sample_fuzz_trials: int = 200, containment_threshold: float = 0.99):
        """
        rules_df: DataFrame with at least columns: rule_id, pattern, action, severity, category
                  optionally: phase, priority, flags
        traffic_df: DataFrame with at least columns: transaction_id, request_uri, user_agent, matched_data, rule_id (may be '-')
        """
        self.rules_df = rules_df.copy()
        self.traffic_df = traffic_df.copy()
        self.relationships: List[Dict] = []
        self.enable_ai = enable_ai
        self.sample_fuzz_trials = sample_fuzz_trials
        self.containment_threshold = containment_threshold
        self.shadowed_rules_set: set = set()

        # AI processor updated to use Groq
        if enable_ai:
            try:
                self.ai_processor = RuleAnalysisAIProcessor(rules_df=self.rules_df)
            except Exception as e:
                logger.warning(f"AI processor initialization failed: {e}")
                self.ai_processor = None
        else:
            self.ai_processor = None

        # Normalization / defaults for rules_df expected columns
        for col, default in [('phase', 2), ('priority', 1000), ('flags', '')]:
            if col not in self.rules_df.columns:
                self.rules_df[col] = default

        # Precompile regexes (safe compile with fallback)
        self._compile_rule_regexes()

        # Simulate matching matrix: rule_id -> set(transaction_id)
        self.match_matrix = self._build_match_matrix()

    def _compile_rule_regexes(self):
        """Precompile regex for each rule row and store in rules_df['_re']"""
        compiled = []
        for _, row in self.rules_df.iterrows():
            pat = str(row.get('pattern', ''))
            flags_str = str(row.get('flags', '')) or ''
            flags = 0
            if 'i' in flags_str.lower():
                flags |= re.IGNORECASE
            # try both search and fullmatch depending on likely usage (we use search)
            try:
                cre = re.compile(pat, flags)
            except re.error:
                # fallback: escape and compile literal match to avoid crash
                try:
                    cre = re.compile(re.escape(pat), flags)
                except Exception:
                    cre = None
            compiled.append(cre)
        self.rules_df['_re'] = compiled

    def _rule_order_key(self, row):
        """Sort key for execution order: (phase asc, priority asc)"""
        return (int(row.get('phase', 2) or 2), int(row.get('priority', 1000) or 1000))

    def _build_match_matrix(self) -> Dict[str, set]:
        """
        For every rule in rules_df, scan traffic and mark which transaction_ids it would match.
        Returns dict rule_id -> set(transaction_id)
        """
        matrix = defaultdict(set)
        # ensure traffic has transaction_id and request_uri
        if 'transaction_id' not in self.traffic_df.columns:
            self.traffic_df['transaction_id'] = range(len(self.traffic_df))  # fallback index
        if 'request_uri' not in self.traffic_df.columns:
            # attempt common alternatives
            raise ValueError("traffic_df must contain 'request_uri' column")

        # Pre-extract request strings to check (could include user_agent, body if available)
        def _row_request_text(row):
            # combine useful fields to maximize match chances
            parts = []
            for c in ('request_uri', 'user_agent', 'matched_data'):
                if c in row and pd.notna(row[c]):
                    parts.append(str(row[c]))
            return ' '.join(parts)

        request_texts = []
        txids = []
        for _, t in self.traffic_df.iterrows():
            txids.append(t['transaction_id'])
            request_texts.append(_row_request_text(t))

        # For each rule, test against all request_texts
        for _, rule in self.rules_df.iterrows():
            rule_id = str(rule['rule_id'])
            cre = rule['_re']
            if cre is None:
                continue
            for tid, text in zip(txids, request_texts):
                try:
                    if cre.search(text):
                        matrix[rule_id].add(tid)
                except Exception:
                    # ignore problematic matches
                    continue
        return matrix

    # ---------------------------
    # Public analysis entry point (modified)
    # ---------------------------
    def analyze_all_relationships(self, analysis_types: List[str]) -> Dict:
        """
        Analyze relationships across ALL rules in rules_df (not just those triggered).
        analysis_types: list like ['SHD','RXD','COR','SUB']
        """
        ordered_rules = sorted(self.rules_df.to_dict('records'), key=self._rule_order_key)
        rule_ids = [str(r['rule_id']) for r in ordered_rules]
        logger.info(f"Analyzing {len(rule_ids)} rules (from rules_df).")

        self.shadowed_rules_set = set()  # track shadowed rules

        for i, rule_a in enumerate(rule_ids):
            if rule_a in self.shadowed_rules_set:
                continue  # skip any rule that is already shadowed

            for rule_b in rule_ids[i+1:]:
                if rule_b in self.shadowed_rules_set:
                    continue  # optional: skip analyzing shadowed B rules too

                rels = self.analyze_rule_pair(rule_a, rule_b, analysis_types, ordered_rules)
                for r in rels:
                    self.relationships.append(r)
                    # Track shadowed rules immediately
                    if r.get('relationship_type') == 'SHD' and r.get('rule_b'):
                        self.shadowed_rules_set.add(r['rule_b'])

        base_results = self.compile_results()

        # AI enhancement if available
        if self.enable_ai and self.ai_processor and getattr(self.ai_processor, 'ai_available', False):
            try:
                enhanced = self.ai_processor.enhance_analysis_with_ai(base_results, self.traffic_df)
                return enhanced
            except Exception as e:
                logger.error(f"AI enhancement failed: {e}")
                base_results['ai_available'] = False
                base_results['ai_error'] = str(e)
                return base_results

        base_results['ai_available'] = False
        return base_results

    # ---------------------------
    # Pairwise analysis
    # ---------------------------
    def analyze_rule_pair(self, rule_a: str, rule_b: str, analysis_types: List[str], ordered_rules: List[Dict]) -> List[Dict]:
        relationships = []

        # gather rule metadata from rules_df
        row_a = self.rules_df[self.rules_df['rule_id'].astype(str) == str(rule_a)]
        row_b = self.rules_df[self.rules_df['rule_id'].astype(str) == str(rule_b)]
        if row_a.empty or row_b.empty:
            return relationships
        row_a = row_a.iloc[0].to_dict()
        row_b = row_b.iloc[0].to_dict()

        # simulated request sets
        set_a = self.match_matrix.get(str(rule_a), set())
        set_b = self.match_matrix.get(str(rule_b), set())

        # provide counts for logging/evidence
        logger.debug(f"Analyzing pair {rule_a} ({len(set_a)}) vs {rule_b} ({len(set_b)})")

        # Shadowing: check whether earlier rules (by phase/priority) cover B's matches
        if 'SHD' in analysis_types:
            sh = self._detect_shadowing(rule_a, rule_b, row_a, row_b, set_a, set_b, ordered_rules)
            if sh:
                relationships.append(sh)

        # Redundancy: co-occurrence > threshold
        if 'RXD' in analysis_types:
            rx = self._detect_redundancy(rule_a, rule_b, row_a, row_b, set_a, set_b)
            if rx:
                relationships.append(rx)

        # Correlation
        if 'COR' in analysis_types:
            co = self._detect_correlation(rule_a, rule_b, row_a, row_b, set_a, set_b)
            if co:
                relationships.append(co)

        # Subsumption/generalization (A subsumes B or vice-versa)
        if 'SUB' in analysis_types:
            sub = self._detect_subsumption(rule_a, rule_b, row_a, row_b, set_a, set_b)
            if sub:
                relationships.extend(sub)  # could contain up to two entries (A->B and B->A)

        return relationships

    # ---------------------------
    # Relationship detectors
    # ---------------------------
    def _detect_shadowing(self, rule_a, rule_b, meta_a, meta_b, set_a, set_b, ordered_rules) -> Dict:
        """
        Determine if rule_a shadows rule_b:
        - rule_a must be earlier in execution order than rule_b
        - For (nearly) all simulated B-matches, at least one earlier rule (including A) matched first and has blocking action
        """
        # find ordering positions
        rule_order = [str(r['rule_id']) for r in ordered_rules]
        try:
            pos_a = rule_order.index(str(rule_a))
            pos_b = rule_order.index(str(rule_b))
        except ValueError:
            return None
        if pos_a >= pos_b:
            return None  # A doesn't execute before B so cannot shadow

        # For each tx in set_b, check if any earlier rule would have matched it (simulate execution)
        earlier_rules = rule_order[:pos_b]  # rules that execute before B
        blocked_count = 0
        total_b = len(set_b) or 1
        evidence_tx = []
        for tx in set_b:
            # is there an earlier rule that matches tx and that earlier rule's action is blocking?
            matched_earlier = False
            for er in earlier_rules:
                if tx in self.match_matrix.get(er, set()):
                    # check action of that earlier rule
                    er_action = self._get_rule_meta(er, 'action')
                    if er_action and str(er_action).lower() in ('block', 'blocked', 'deny'):
                        matched_earlier = True
                        break
                    else:
                        # matched earlier but not blocking - still may prevent B if phase stops request; we treat non-block as non-shadow for now
                        matched_earlier = False
            if matched_earlier:
                blocked_count += 1
                evidence_tx.append(tx)

        shadow_confidence = blocked_count / total_b
        if shadow_confidence > 0.75 and len(evidence_tx) > 0:  # conservative threshold
            return {
                'relationship_type': 'SHD',
                'rule_a': str(rule_a),
                'rule_b': str(rule_b),
                'confidence': shadow_confidence,
                'evidence_count': len(evidence_tx),
                'evidence_tx_ids': evidence_tx[:10],
                'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                'description': (f"Rule {rule_a} (earlier) blocks ~{shadow_confidence:.1%} of requests that would match {rule_b}.")
            }
        return None

    def _detect_redundancy(self, rule_a, rule_b, meta_a, meta_b, set_a, set_b) -> Dict:
        """If two rules co-occur almost always (high Jaccard / co-occurrence), they are redundant candidates."""
        if not set_a and not set_b:
            return None
        intersection = len(set_a & set_b)
        co_occurrence_rate = intersection / max(1, min(len(set_a), len(set_b)))
        # Jaccard useful as well
        union = len(set_a | set_b)
        jaccard = intersection / union if union else 0.0
        if co_occurrence_rate > 0.85 and jaccard > 0.7:
            return {
                'relationship_type': 'RXD',
                'rule_a': str(rule_a),
                'rule_b': str(rule_b),
                'confidence': float(co_occurrence_rate),
                'evidence_count': intersection,
                'jaccard': float(jaccard),
                'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                'description': f"Rules {rule_a} and {rule_b} trigger together {co_occurrence_rate:.1%} of the time (jaccard {jaccard:.2f})."
            }
        return None

    def _detect_correlation(self, rule_a, rule_b, meta_a, meta_b, set_a, set_b) -> Dict:
        total = max(1, len(self.traffic_df))
        intersection = len(set_a & set_b)
        actual = intersection / total
        expected = (len(set_a) / total) * (len(set_b) / total)
        if expected == 0:
            return None
        lift = actual / expected if expected > 0 else float('inf')
        # require both some support and lift > threshold
        if intersection >= 3 and lift > 2.0:
            # normalized confidence between 0..1 (cap)
            confidence = min((math.log2(lift) / 5.0) + 0.2, 1.0)
            return {
                'relationship_type': 'COR',
                'rule_a': str(rule_a),
                'rule_b': str(rule_b),
                'confidence': confidence,
                'evidence_count': intersection,
                'lift': float(lift),
                'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                'description': f"Rules {rule_a} and {rule_b} co-occur {intersection} times, lift {lift:.2f}."
            }
        return None

    def _detect_subsumption(self, rule_a, rule_b, meta_a, meta_b, set_a, set_b) -> List[Dict]:
        """
        Approximate containment: if virtually all B-matches are also matches of A (on traffic and fuzz), then A subsumes B.
        We test both directions (A subsumes B) and (B subsumes A).
        """
        results = []
        # helper to test A contains B
        def a_contains_b(set_a_local, set_b_local, meta_a_local, meta_b_local):
            if not set_b_local:
                return False, 0.0, []
            # proportion of B's matched tx that are also matched by A
            traffic_contained = len(set_a_local & set_b_local) / len(set_b_local)
            # fuzzing: generate random strings from B matched_data (fallback to random if none)
            fuzz_contained = self._fuzz_containment_test(meta_a_local, meta_b_local, trials=self.sample_fuzz_trials)
            # combine conservatively: require both to be high or traffic high
            combined = max(traffic_contained, fuzz_contained)
            evidence = list(set_a_local & set_b_local)[:10]
            return (combined >= self.containment_threshold), combined, evidence

        # A -> B?
        ok, conf, evidence = a_contains_b(set_a, set_b, meta_a, meta_b)
        if ok:
            results.append({
                'relationship_type': 'SUB',  # A subsumes B
                'subsuming_rule': str(rule_a),
                'subsumed_rule': str(rule_b),
                'confidence': conf,
                'evidence_count': len(evidence),
                'evidence_tx_ids': evidence,
                'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                'description': f"Rule {rule_a} likely subsumes (generalizes) rule {rule_b} (confidence {conf:.2f})."
            })

        # B -> A?
        ok2, conf2, evidence2 = a_contains_b(set_b, set_a, meta_b, meta_a)
        if ok2:
            results.append({
                'relationship_type': 'SUB',
                'subsuming_rule': str(rule_b),
                'subsumed_rule': str(rule_a),
                'confidence': conf2,
                'evidence_count': len(evidence2),
                'evidence_tx_ids': evidence2,
                'conflicting_fields': self.get_conflicting_fields(rule_b, rule_a),
                'description': f"Rule {rule_b} likely subsumes (generalizes) rule {rule_a} (confidence {conf2:.2f})."
            })

        return results

    def _fuzz_containment_test(self, meta_sub, meta_spec, trials=100) -> float:
        """
        Lightweight fuzz test: take matched_data from spec (if any) as seeds, mutate them, and test whether sub's regex matches.
        Returns proportion of spec-derived fuzz samples that sub also matches.
        """
        # Attempt to extract some example strings from traffic for the 'spec' rule
        spec_id = str(meta_spec.get('rule_id'))
        sub_id = str(meta_sub.get('rule_id'))
        spec_txids = list(self.match_matrix.get(spec_id, []))
        if not spec_txids:
            # no real examples -> do random trials (low confidence)
            hits = 0
            for _ in range(min(trials, 50)):
                s = ''.join(chr(randint(33,126)) for _ in range(randint(5,40)))
                try:
                    if self.rules_df[self.rules_df['rule_id'].astype(str) == sub_id]['_re'].iloc[0].search(s):
                        hits += 1
                except Exception:
                    pass
            return hits / max(1, min(trials, 50))
        # collect sample strings from traffic rows
        examples = []
        for tx in spec_txids[:min(200, len(spec_txids))]:
            row = self.traffic_df[self.traffic_df['transaction_id'] == tx]
            if row.empty:
                continue
            text = ' '.join(str(row.iloc[0].get(c, '')) for c in ('matched_data', 'request_uri', 'user_agent'))
            if text:
                examples.append(text)
        if not examples:
            return 0.0
        hits = 0
        sub_re = self.rules_df[self.rules_df['rule_id'].astype(str) == sub_id]['_re'].iloc[0]
        for s in examples[:min(len(examples), trials)]:
            try:
                if sub_re.search(s):
                    hits += 1
            except Exception:
                continue
        return hits / len(examples[:min(len(examples), trials)])

    # ---------------------------
    # Utilities & reporting
    # ---------------------------
    def _get_rule_meta(self, rule_id: str, field: str):
        row = self.rules_df[self.rules_df['rule_id'].astype(str) == str(rule_id)]
        if row.empty:
            return None
        return row.iloc[0].get(field)

    def find_common_requests(self, rule_a: str, rule_b: str) -> List:
        """Find requests (transaction_id) where both rules would match (based on simulated matrix)"""
        a = self.match_matrix.get(str(rule_a), set())
        b = self.match_matrix.get(str(rule_b), set())
        common = list(a & b)
        logger.debug(f"Common requests between {rule_a} and {rule_b}: {len(common)}")
        return common

    def get_conflicting_fields(self, rule_a: str, rule_b: str) -> Dict:
        """Identify overlapping/conflicting metadata fields between two rules (from rules_df)"""
        a = self.rules_df[self.rules_df['rule_id'].astype(str) == str(rule_a)]
        b = self.rules_df[self.rules_df['rule_id'].astype(str) == str(rule_b)]
        if a.empty or b.empty:
            return {}
        a = a.iloc[0]
        b = b.iloc[0]
        conflicting = {}
        if a.get('category') and b.get('category') and a['category'] == b['category']:
            conflicting['category'] = f"Both category: {a['category']}"
        if a.get('severity') and b.get('severity') and a['severity'] == b['severity']:
            conflicting['severity'] = f"Both severity: {a['severity']}"
        if a.get('action') and b.get('action') and a['action'] == b['action']:
            conflicting['action'] = f"Both action: {a['action']}"
        return conflicting

    def extract_rule_patterns(self, rule_id: str) -> Dict:
        """Return rule metadata (pattern, severity, category) from rules_df"""
        row = self.rules_df[self.rules_df['rule_id'].astype(str) == str(rule_id)]
        if row.empty:
            return {}
        r = row.iloc[0]
        return {
            'pattern': r.get('pattern'),
            'attack_type': r.get('category', 'Unknown'),
            'severity': r.get('severity', 'Unknown'),
            'action': r.get('action', 'Unknown'),
        }

    def compile_results(self) -> Dict:
        relationships_by_type = {}
        for rel in self.relationships:
            rel_type = rel['relationship_type']
            relationships_by_type.setdefault(rel_type, []).append(rel)

        rule_count = len(self.rules_df)
        return {
            'total_rules': rule_count,
            'total_relationships': len(self.relationships),
            'relationships': relationships_by_type,
            'shd_count': len(relationships_by_type.get('SHD', [])),
            'rxd_count': len(relationships_by_type.get('RXD', [])),
            'sub_count': len(relationships_by_type.get('SUB', [])),
            'cor_count': len(relationships_by_type.get('COR', [])),
            'recommendations': self.generate_recommendations(),
            'sample_rules': list(self.rules_df['rule_id'].astype(str).values)[:10],
        }

    def generate_recommendations(self) -> List[Dict]:
        recs = []
        shd = [r for r in self.relationships if r['relationship_type'] == 'SHD']
        if shd:
            recs.append({
                'type': 'Remove/Review Shadowed Rules',
                'description': f"{len(shd)} rules appear shadowed by earlier blocking rules. Review before removal.",
                'impact': 'Performance improvement likely; verify behaviour with canary tests.'
            })
        rxd = [r for r in self.relationships if r['relationship_type'] == 'RXD']
        if rxd:
            recs.append({
                'type': 'Merge/Consolidate Redundant Rules',
                'description': f"{len(rxd)} redundant pairs found. Consider merging patterns or removing duplicates.",
                'impact': 'Simplicity & maintenance reduction.'
            })
        sub = [r for r in self.relationships if r['relationship_type'] == 'SUB']
        if sub:
            recs.append({
                'type': 'Specialize or Keep Specific Rules',
                'description': f"{len(sub)} subsumption cases. Consider keeping specialized rules if they provide different actions or clearer diagnostic messages.",
                'impact': 'Avoid losing fine-grained detection.'
            })
        cor = [r for r in self.relationships if r['relationship_type'] == 'COR']
        if cor and not recs:
            recs.append({
                'type': 'Review Correlated Rules',
                'description': f"{len(cor)} correlated relationships. Review for potential tuning or ordering changes.",
                'impact': 'Potential performance/security tuning.'
            })
        if not recs:
            recs.append({
                'type': 'No obvious optimizations found',
                'description': 'No high-confidence relationships detected with current thresholds.',
                'impact': 'No immediate action recommended.'
            })
        return recs
