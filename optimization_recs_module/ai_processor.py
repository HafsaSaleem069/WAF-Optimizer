# ai_processor.py

import json
import logging
import pandas as pd
from typing import Dict, List
from .groq_client import GroqAIClient # Import the client


logger = logging.getLogger(__name__)

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
            "description": row.get("description", ""),
            "severity": row.get("severity", ""),
            "action": row.get("action", ""),
            "phase": row.get("phase", ""),
            "pattern": row.get("pattern", ""),
        }
    
    def enhance_analysis_with_ai(self, analysis_results: Dict, traffic_df: pd.DataFrame) -> Dict:
        # ... (error checks remain the same) ...

        try:
            # Create a shallow copy of the relationships structure to modify it
            relationships_to_enhance = analysis_results.get("relationships", {}).copy()
            
            # Use an index to track which list we are modifying for the final output
            for rel_type, rel_list in relationships_to_enhance.items():
                
                # Iterate over the list by index to directly modify the relationship object
                for i in range(len(rel_list)):
                    rel = rel_list[i] # Get the relationship dict

                    rule_a_id = rel.get("rule_a")
                    rule_b_id = rel.get("rule_b")

                    if not rule_a_id or not rule_b_id:
                        continue
                    
                    # ... (Extraction of rule_a_data, rule_b_data, and context remains the same) ...
                    # ... (The logic for context preparation is unchanged) ...

                    rule_a_data = self._get_rule_data(rule_a_id)
                    rule_b_data = self._get_rule_data(rule_b_id)
                    context = {
                        "relationship_type": rel_type,
                        "confidence": rel.get("confidence"),
                        "evidence_count": rel.get("evidence_count"),
                        "conflicting_fields": rel.get("conflicting_fields", {}),
                        "description": rel.get("description", "")
                    }
                    
                    try:
                        ai_response = None
                        
                        # 🔹 Redundant Rules (RXD)
                        if rel_type in ("RXD", "SHD"): # Use optimize_redundant_rules for both
                            ai_response = self.ai_client.optimize_redundant_rules(
                                rule_a_id, rule_b_id, rel_type, rule_a_data, rule_b_data, context
                            )

                        # 🔹 Correlated Rules (COR)
                        elif rel_type == "COR":
                            # Use the existing prompt logic for correlation
                            user_prompt = (
                                f"Rules {rule_a_id} and {rule_b_id} often trigger together (correlated). "
                                f"Suggest optimization or grouping ideas.\n\n"
                                f"Rule A: {json.dumps(rule_a_data, indent=2, default=str)}\n"
                                f"Rule B: {json.dumps(rule_b_data, indent=2, default=str)}\n"
                                f"Traffic Context: {json.dumps(context, indent=2, default=str)}"
                            )
                            # NOTE: Assuming the AI client's make_request returns a dict that is compatible
                            ai_response = self.ai_client.make_request(
                                "You are a ModSecurity correlation analyzer. Return a JSON structure with 'action': 'GROUP_OR_REVIEW', 'explanation', and 'optimized_rule'.",
                                user_prompt,
                                temperature=0.4,
                                max_tokens=800
                            )
                        
                        # --- KEY MODIFICATION HERE ---
                        if ai_response:
                            rel_list[i]['ai_suggestion'] = ai_response
                        else:
                            rel_list[i]['ai_suggestion'] = {"action": "NO_SUGGESTION", "explanation": "AI did not provide a specific response.", "optimized_rule": "N/A"}
                        # -----------------------------

                    except Exception as e:
                        logger.error(f"AI request failed for {rule_a_id} vs {rule_b_id} ({rel_type}): {e}")
                        rel_list[i]['ai_suggestion'] = {"action": "AI_ERROR", "explanation": f"AI processing error: {str(e)}", "optimized_rule": "N/A"}

            # Merge the modified relationships back into the analysis_results
            analysis_results["relationships"] = relationships_to_enhance
            analysis_results["ai_available"] = True
            print(f"✅ AI enhancement completed successfully")
            return analysis_results

        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            analysis_results["ai_available"] = False
            analysis_results["ai_error"] = str(e)
            return analysis_results