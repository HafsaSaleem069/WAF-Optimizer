# groq_client.py

import requests
import os
import json
import logging
import re
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GroqAIClient:
    """Centralized AI client for all WAF optimization tasks using Groq API"""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1"
        
        # --- NEW --- Variables to store the current rule IDs for parsing
        self.rule_a_id = "N/A"
        self.rule_b_id = "N/A"
        # --- END NEW ---
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
            raise ValueError("Groq API key not configured")
        
        # Use only the model that we know works
        self.model = "llama-3.3-70b-versatile"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Test API connection on initialization
        self._test_api_connection()
    
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
            
            print("Raw API Response:") # Or use a proper logging library
            print(json.dumps(result, indent=4))

            # 💡 NOTE: The model's response structure changes. We now grab 'content'.
            return self._parse_text_response(result['choices'][0]['message']['content']) 
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_response = response.json()
                error_detail = f" - {error_response}"
            except:
                error_detail = f" - Response: {response.text}"
            
            logger.error(f"Groq API HTTP error {response.status_code}: {e}{error_detail}")
            raise Exception(f"Groq API HTTP error {response.status_code}: {e}")
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise Exception(f"Groq API error: {e}")
    
    def optimize_redundant_rules(self, rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context):
        """Specific method for rule optimization with labeled text output"""
        
        system_prompt = """
        You are a WAF rule optimization expert. Your task is to analyze two rules and provide a single, prioritized suggestion to merge rule patterns into one rule or remove one rule.
        
        # 🚨 CRITICAL: The entire response MUST be wrapped in a single, unadorned JSON object.
        
        The returned response MUST be of the following json format structure, enclosed in triple backticks:
        
        {
            "explanation": "<Provide any exlanation here>",
            "optimized_rule": "<complete ModSecurity rule syntax>",
            "action": "<MERGE|REMOVE_RULE_A|REMOVE_RULE_B|KEEP_BOTH>"
        }

        Ensure that the "optimized_rule" field contains valid ModSecurity rule syntax if the action is MERGE. If the action is to remove a rule, the "optimized_rule" field can be an empty string.
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
        # 💡 NEW: Extract the full pattern, description, action, and phase
        rule_a_details = {
            'description': rule_a_data.get('description', 'No description'),
            'action': rule_a_data.get('action', 'Unknown'),
            'phase': rule_a_data.get('phase', 'Unknown'),
            'pattern': rule_a_data.get('pattern', 'No pattern provided. Cannot merge.'), # CRITICAL for merging
            'attack_type': rule_a_data.get('attack_type', 'Unknown'),
            'severity': rule_a_data.get('severity', 'Unknown'),
            'matched_data': rule_a_data.get('matched_data', 'None'),
            'trigger_count': rule_a_data.get('trigger_count', 0)
        }
        rule_b_details = {
            'description': rule_b_data.get('description', 'No description'),
            'action': rule_b_data.get('action', 'Unknown'),
            'phase': rule_b_data.get('phase', 'Unknown'),
            'pattern': rule_b_data.get('pattern', 'No pattern provided. Cannot merge.'), # CRITICAL for merging
            'attack_type': rule_b_data.get('attack_type', 'Unknown'),
            'severity': rule_b_data.get('severity', 'Unknown'),
            'matched_data': rule_b_data.get('matched_data', 'None'),
            'trigger_count': rule_b_data.get('trigger_count', 0)
        }

        prompt = f"""
        Analyze these two WAF rules with a {relationship_type} relationship and suggest a single prioritized suggestion to merge the patterns into one rule or remove one rule.

        RULE A (ID: {rule_a_id}):
        - Description: {rule_a_details['description']}
        - Action: {rule_a_details['action']} (Phase: {rule_a_details['phase']})
        - Pattern : {rule_a_details['pattern']}
        ---
        - Attack Type: {rule_a_details['attack_type']}
        - Severity: {rule_a_details['severity']}
        - Matched Patterns: {rule_a_details['matched_data']}
        - Trigger Count: {rule_a_details['trigger_count']}

        RULE B (ID: {rule_b_id}):
        - Description: {rule_b_details['description']}
        - Action: {rule_b_details['action']} (Phase: {rule_b_details['phase']})
        - Pattern: {rule_b_details['pattern']}
        ---
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
    
    def _replace_ids_in_result(self, result):
        """Replaces generic Rule A/B references with actual IDs in the final result dictionary."""
        
        rule_a_str = f"Rule A (ID: {self.rule_a_id})"
        rule_b_str = f"Rule B (ID: {self.rule_b_id})"
        
        # Perform replacements on text fields
        for key in ['explanation', 'optimized_rule']:
            if key in result and isinstance(result[key], str):
                text = result[key]
                # Replace specific tags with ID strings
                text = text.replace("RULE A", rule_a_str).replace("Rule A", rule_a_str)
                text = text.replace("RULE B", rule_b_str).replace("Rule B", rule_b_str)
                # Replace generic rule name references
                text = text.replace("remove Rule A", f"remove {rule_a_str}")
                text = text.replace("remove Rule B", f"remove {rule_b_str}")
                
                result[key] = text
        
        # Perform replacements on implementation steps (list)
        if 'implementation_steps' in result and isinstance(result['implementation_steps'], list):
            new_steps = []
            for step in result['implementation_steps']:
                new_step = step.replace("REMOVE_RULE_A", f"REMOVE_RULE_A ({rule_a_str})")
                new_step = new_step.replace("REMOVE_RULE_B", f"REMOVE_RULE_B ({rule_b_str})")
                new_steps.append(new_step)
            result['implementation_steps'] = new_steps
            
        return result


    def _parse_text_response(self, ai_response):
        """
        Aggressively extracts the primary suggestion by identifying the first
        complete JSON structure found in the raw text, as the AI is instructed
        to return the final suggestion in JSON format.
        """
        raw_text = ai_response.strip()
        
        # 1. Initialize fallback result structure with a clear failure message
        result = {
            "optimized_rule": "N/A (Pattern not found)",
            "action": "REVIEW_MANUALLY",
            "explanation": "AI output could not be parsed into the target JSON structure. Requires manual review.",
            "security_impact": "Requires manual review.",
            "performance_improvement": "N/A",
            "implementation_steps": ["Check raw response for suggested actions."]
        }

        # 2. **Primary Extraction: Find and parse the first JSON block**
        # This regex specifically targets JSON enclosed in triple backticks (```json ... ``` or ``` ... ```).
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL | re.IGNORECASE)
        
        parsed_json_successful = False
        if json_match:
            json_str = json_match.group(1).strip()
            
            # --- CRITICAL CLEANUP: Fix unescaped quotes (ModSecurity rule syntax) within JSON values ---
            json_str_cleaned = json_str
            
            # Regex replacement function to escape double quotes inside a string value
            # It finds: "key" : "value_with_inner_quotes"
            def escape_inner_quotes_callback(match):
                key = match.group(1)
                # The value string (content between the final quotes)
                value_content = match.group(2) 
                # Replace internal unescaped double quotes with escaped quotes
                escaped_content = value_content.replace('"', '\\"')
                # Reconstruct the key-value pair
                return f'{key}"{escaped_content}"'

            # Apply cleanup to 'explanation' field
            # CHANGED: Use (.*?) for non-greedy match of the value
            json_str_cleaned = re.sub(
                r'("explanation"\s*:\s*)"(.*?)"', 
                escape_inner_quotes_callback,
                json_str_cleaned,
                count=1,
                flags=re.DOTALL
            )

            # Apply cleanup to 'optimized_rule' field
            # CRITICAL CHANGE: Use (.*?) for non-greedy match of the value
            json_str_cleaned = re.sub(
                r'("optimized_rule"\s*:\s*)"(.*?)"', 
                escape_inner_quotes_callback,
                json_str_cleaned,
                count=1,
                flags=re.DOTALL
            )
            # -----------------------------------------------------------------------------------------
            
            try:
                # Use the cleaned string for parsing
                parsed_json = json.loads(json_str_cleaned)
                
                # Check for the required fields and populate the final result
                if all(key in parsed_json for key in ["explanation", "optimized_rule", "action"]):
                    result["explanation"] = parsed_json["explanation"].strip()
                    
                    # If the optimized rule is an empty string, set a more helpful message
                    optimized_rule_content = parsed_json["optimized_rule"].strip()
                    
                    # This logic handles cases where the rule is simply REMOVED
                    if not optimized_rule_content and result.get('action') == "REMOVE_RULE_B":
                        result["optimized_rule"] = f"No optimized rule is provided as Rule B (ID: {self.rule_b_id}) will be removed, and Rule A (ID: {self.rule_a_id}) will remain unchanged."
                    elif not optimized_rule_content and result.get('action') == "REMOVE_RULE_A":
                        # Added logic for REMOVE_RULE_A as well
                        result["optimized_rule"] = f"No optimized rule is provided as Rule A (ID: {self.rule_a_id}) will be removed, and Rule B (ID: {self.rule_b_id}) will remain unchanged."
                    else:
                        result["optimized_rule"] = optimized_rule_content
                        
                    result["action"] = parsed_json["action"].strip().upper()
                    
                    # Set default success values for other fields
                    result["security_impact"] = "Action based on AI recommendation."
                    result["performance_improvement"] = "Expected by AI recommendation."
                    result["implementation_steps"] = [f"Implement action: {result['action']}", "Check optimized_rule for syntax."]
                    
                    parsed_json_successful = True
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI JSON block after cleanup: {e}")
                pass # Fall through to the next steps if JSON parsing failed

        # 3. **Fallback Extraction (If JSON was not found or failed to parse)**
        if not parsed_json_successful:
            if re.search(r'REMOVE_RULE_A', raw_text, re.IGNORECASE):
                result['action'] = "REMOVE_RULE_A"
                result['explanation'] = "AI suggests removing Rule A, action extracted from text."
                result['optimized_rule'] = "Keep Rule B as is, remove Rule A."
            elif re.search(r'REMOVE_RULE_B', raw_text, re.IGNORECASE):
                result['action'] = "REMOVE_RULE_B"
                result['explanation'] = "AI suggests removing Rule B, action extracted from text."
                result['optimized_rule'] = "Keep Rule A as is, remove Rule B."
            elif re.search(r'MERGE|combine', raw_text, re.IGNORECASE):
                result['action'] = "MERGE"
                result['explanation'] = "AI suggests merging the two rules, action extracted from text. Requires manual check for merged rule syntax."
            # Note: Default action is REVIEW_MANUALLY if no clear action is found.


        # 4. Final mapping and ID replacement.
        final_result = {
            "optimized_rule": result['optimized_rule'],
            "action": result['action'],
            "explanation": result['explanation'],
            "security_impact": result.get('security_impact', 'N/A'),
            "performance_improvement": result.get('performance_improvement', 'N/A'),
            "implementation_steps": result.get('implementation_steps', ["Check raw response for suggested actions."])
        }
        
        # Apply the ID replacement logic to all output fields
        return self._replace_ids_in_result(final_result)