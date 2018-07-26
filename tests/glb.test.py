def create_google_load_balancer(self):
    bindings = self._bindings
    load_balancer_name = bindings['TEST_APP_COMPONENT_NAME']

    spec = {
        'checkIntervalSec': 9,
        'healthyThreshold': 3,
        'unhealthyThreshold': 5,
        'timeoutSec': 2,
        'port': 80
    }

    target_pool_name = '{0}/targetPools/{1}-tp'.format(
        bindings['TEST_REGION'], load_balancer_name)


job = [{
    'cloudProvider': 'gce',
    'provider': 'gce',
    'stack': bindings['TEST_STACK'],
    'detail': bindings['TEST_COMPONENT_DETAIL'],
    'credentials': bindings['GCE_CREDENTIALS'],
    'region': bindings['TEST_GCE_REGION'],
    'ipProtocol': 'TCP',
    'portRange': spec['port'],
    'loadBalancerName': load_balancer_name,
    'healthCheck': {
                'port': spec['port'],
                'timeoutSec': spec['timeoutSec'],
                'checkIntervalSec': spec['checkIntervalSec'],
                'healthyThreshold': spec['healthyThreshold'],
                'unhealthyThreshold': spec['unhealthyThreshold'],
    },
    'type': 'upsertLoadBalancer',
            'availabilityZones': {bindings['TEST_GCE_REGION']: []},
            'user': '[anonymous]'
}],

description = 'Create Load Balancer: ' + load_balancer_name,
application = bindings(['TEST_APP'])

builder = gcp_testing.GceContractBuilder(self.gce_observer)
(builder.new_clause_builder('Health Check Added',
                            retryable_for_secs=30)
 .list_resources('http-health-checks')
 .contains_pred_list(
    [json_predicate.PathContainsPredicate(
        'name', '%s-hc' % load_balancer_name),
     json_predicate.DICT_SUBSET(spec)]))
(builder.new_clause_builder('Target Pool Added',
                            retryable_for_secs=30)
 .list_resources('target-pools')
 .contains_path_value('name', '%s-tp' % load_balancer_name))
(builder.new_clause_builder('Forwarding Rules Added',
                            retryable_for_secs=30)
 .list_resources('forwarding-rules')
 .contains_pred_list([
     json_predicate.PathContainsPredicate('name', load_balancer_name),
     json_predicate.PathContainsPredicate('target', target_pool_name)]))

    return service_testing.OperationContract(
        self.new_post_operation(
            title='upsert_load_balancer', data=payload, path='tasks'),
            contract=builder.build())
