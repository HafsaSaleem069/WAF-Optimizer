from dotenv import load_dotenv
load_dotenv()  # ADD THIS LINE

logger = logging.getLogger(__name__)

class DeepSeekAIClient:
    """Centralized AI client for all WAF optimization tasks"""
    
    def __init__(self):
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            logger.warning("DEEPSEEK_API_KEY not found in environment variables")
            raise ValueError("DeepSeek API key not configured")
            
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = "deepseek-chat"
    
    def make_request(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1000):
        """Generic method for all AI requests"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}")
            return self._create_error_response(str(e))
    
    def optimize_redundant_rules(self, rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context):
        """Specific method for rule optimization"""
        system_prompt = """You are a WAF security expert specializing in ModSecurity rule optimization. 
        Provide concise, actionable rule optimization suggestions in valid JSON format.
        Focus on practical improvements that maintain security while reducing redundancy."""
        
        user_prompt = self._build_rule_optimization_prompt(
            rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context
        )
        
        return self.make_request(system_prompt, user_prompt, temperature=0.3, max_tokens=800)
    
    def _build_rule_optimization_prompt(self, rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context):
        """Build the prompt for rule optimization"""
        
        # Extract rule details
        rule_a_details = self._extract_rule_details(rule_a_data)
        rule_b_details = self._extract_rule_details(rule_b_data)
        
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

        Provide a JSON response with these fields:
        - optimized_rule: A complete ModSecurity rule that combines both rules' protection
        - action: Specific instruction (MERGE, REMOVE_RULE_A, REMOVE_RULE_B, KEEP_BOTH)
        - explanation: Brief technical explanation
        - security_impact: How security is maintained or improved
        - performance_improvement: Expected performance gain
        - implementation_steps: Array of step-by-step actions

        Make the optimized rule practical and ready for ModSecurity deployment.
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
    
    def _parse_response(self, ai_response):
        """Parse AI response and ensure valid structure"""
        try:
            suggestion = json.loads(ai_response)
            
            # Ensure required fields exist
            required_fields = ['optimized_rule', 'action', 'explanation']
            for field in required_fields:
                if field not in suggestion:
                    suggestion[field] = f"Missing {field}"
            
            return suggestion
            
        except json.JSONDecodeError:
            return self._create_fallback_suggestion(ai_response)
    
    def _create_error_response(self, error_msg):
        """Create standardized error response"""
        return {
            "error": f"AI service unavailable: {error_msg}",
            "suggestion": "Please try again later or use manual analysis",
            "fallback_mode": True
        }
    
    def _create_fallback_suggestion(self, raw_text):
        """Create structured suggestion from raw text"""
        return {
            "optimized_rule": "# AI suggestion unavailable - manual review required",
            "action": "REVIEW", 
            "explanation": raw_text[:200] + "..." if len(raw_text) > 200 else raw_text,
            "security_impact": "Unknown - requires manual verification",
            "performance_improvement": "Unknown",
            "implementation_steps": [
                "1. Review the AI explanation above",
                "2. Manually create optimized rule",
                "3. Test thoroughly before deployment"
            ]
        }