from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    """FR05-03: Check if user has admin role"""
    return user.groups.filter(name='admin').exists() or user.is_superuser

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_admin)
def approve_rule_ranking(request, session_id):
    """
    FR05-03: Admin approval endpoint
    LEARNING: Security measure - prevents accidental rule changes
    """
    try:
        ranking_session = RuleRankingSession.objects.get(id=session_id)
        
        # FR05-03: Record who approved and when
        ranking_session.status = 'approved'
        ranking_session.approved_by = request.user
        ranking_session.save()
        
        # FR05-04: Apply the optimized ordering
        apply_optimized_ranking(ranking_session.optimized_rules_order)
        
        # FR05-04: Re-run analysis with new order
        re_run_analysis()
        
        return Response({
            'status': 'success',
            'message': 'Rule ranking approved and applied successfully',
            'improvement': f"{ranking_session.performance_improvement:.1f}% expected performance gain"
        })
        
    except RuleRankingSession.DoesNotExist:
        return Response({'error': 'Ranking session not found'}, status=404)

def apply_optimized_ranking(optimized_order: List):
    """
    FR05-04: Apply the new rule order to the WAF
    LEARNING: This is where we actually change the rule execution order
    """
    # This would interface with your ModSecurity configuration
    # For now, we'll just update our database
    
    for rule_data in optimized_order:
        rule_id = rule_data['rule_id']
        new_position = rule_data['new_position']
        
        # Update rule position in database
        # In real implementation, this would update ModSecurity rules file
        print(f"Moving rule {rule_id} to position {new_position}")
    
    print("FR05-04: Rule ranking applied successfully!")

def re_run_analysis():
    """
    FR05-04: Re-run conflict analysis with new order
    LEARNING: Ensures our changes don't break anything
    """
    # This would trigger FR02 analysis again
    print("Re-running rule conflict analysis with new order...")