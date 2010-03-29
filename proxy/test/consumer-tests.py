import unittest
import httplib, urllib
import simplejson as json

from testfixture import CandlepinTests
from candlepinapi import *

class ConsumerTests(CandlepinTests):

    def setUp(self):
        CandlepinTests.setUp(self)

    def test_unbind_by_entitlement(self):
        pools = self.cp.getPools(consumer=self.uuid)
        pool = pools[0]

        self.assertEqual([], self.cp.getEntitlements(self.uuid))

        # First we list all pools available to this consumer:
        virt_host = 'virtualization_host'
        results = self.cp.getPools(consumer=self.uuid)
        pools = {}
        for pool in results:
            pools[pool['productId']] = pool
        self.assertTrue(virt_host in pools)
        #while in theory this could return a different pool object than
        #is used to allocate the entitlement later on, 
        #our default setup means that they should be the same.
        results = self.cp.getPools( consumer=self.uuid,product=virt_host  )
        expected_consumed = results[0]['consumed']

        result = self.cp.getEntitlements(self.uuid)
        self.assertEquals(len(result ),0)
        
        # Request a virtualization_host entitlement:
        result = self.cp.bindPool(self.uuid, pools[virt_host]['id'])
        self.assertTrue('id' in result[0])
        self.assertEquals(virt_host, result[0]['pool']['productId'])
        entitlementId =  result[0]['id']
        consumed = result[0]['pool']['consumed']
        expected_consumed = expected_consumed + 1
        self.assertEquals(expected_consumed,consumed)

        #make sure the number consumed in the pool increased by one
        results = self.cp.getPools( consumer=self.uuid,product=virt_host  )
        self.assertEquals(expected_consumed, results[0]['consumed'])

        # Now list consumer's entitlements:
        result = self.cp.getEntitlements(self.uuid)
        self.assertEquals(len(result),1)
        
        #for p in result:
        #    self.cp.unBindEntitlement( p['entitlement']['id'])
        #    expected_consumed -= 1

        self.cp.unBindEntitlement( entitlementId )
        expected_consumed -= 1

        result = self.cp.getEntitlements(self.uuid)
        self.assertEquals(len(result),0)
        results = self.cp.getPools( consumer=self.uuid,product=virt_host  )
        self.assertEquals(expected_consumed, results[0]['consumed'])


    def test_list_cert_serials(self):
        result = self.cp.getCertificateSerials(self.uuid)
        print result
        #self.assertTrue('serial' in result)
        #serials = result['serial']
        for serial in result:
            self.assertTrue('serial' in serial)
        # TODO: Could use some more testing here once entitlement certs
        # are actually being generated.

    def test_list_certs(self):
        self.cp.bindProduct(self.uuid, 'monitoring')
        self.cp.bindProduct(self.uuid, 'virtualization_host')

        cert_list = self.cp.getCertificates(self.uuid)
        self.assertEquals(2, len(cert_list))
        last_key = None
        last_cert = None
        for cert in cert_list:
            print
            print "cert from cert_list"
            print cert
            self.assert_ent_cert_struct(cert)
            print

            if last_key is not None:
                self.assertEqual(last_key, cert['key'])
                self.assertNotEqual(last_cert, cert['cert'])
                self.assertEquals(last_key, self.id_cert['key'])
            last_key = cert['key']
            last_cert = cert['cert']

    def test_list_certs_serial_filtering(self):
        self.cp.bindProduct(self.uuid, 'monitoring')
        self.cp.bindProduct(self.uuid, 'virtualization_host')
        self.cp.bindProduct(self.uuid, 'provisioning')

        cert_list = self.cp.getCertificates(self.uuid)
        self.assertEquals(3, len(cert_list))
        for cert in cert_list:
            print
            print "cert from cert_list"
            print cert
            self.assert_ent_cert_struct(cert)
            print

        serials = [cert_list[0]['serial'], cert_list[1]['serial']]
        cert_list = self.cp.getCertificates(self.uuid, serials)
        self.assertEquals(2, len(cert_list))

    def test_uuid(self):
        self.assertTrue(self.uuid != None)

    def test_bind_by_entitlement_pool(self):
        # First we list all pools available to this consumer:
        virt_host = 'virtualization_host'
        results = self.cp.getPools(consumer=self.uuid)
        pools = {}
        for pool in results:
            pools[pool['productId']] = pool
        self.assertTrue(virt_host in pools)

        # Request a virtualization_host entitlement:
        results = self.cp.bindPool(self.uuid, pools[virt_host]['id'])
        print "virt host"
        print results
        for result in results:
            self.assertTrue('id' in result)
            self.assertEquals(virt_host, result['pool']['productId'])

        # Now list consumer's entitlements:
        result = self.cp.getEntitlements(self.uuid)
        print "Consumer's entitlements:"
        print result

    # Just need to request a product that will fail, for now creating a virt
    # system and trying to give it virtualization_host:
    def test_failed_bind_by_entitlement_pool(self):
        # Create a virt system:
        virt_uuid = self.create_consumer(consumer_type="virt_system")[0]

        # Get pool ID for virtualization_host:
        virt_host = 'virtualization_host'
        results = self.cp.getPools(product=virt_host)
        print("Virt host pool: %s" % results)
        self.assertEquals(1, len(results))
        pool_id = results[0]['id']

        # Request a virtualization_host entitlement:
        try:
            self.cp.bindPool(virt_uuid, pool_id)
            self.fail("Shouldn't have made it here.")
        except CandlepinException, e:
            self.assertEquals('rulefailed.virt.ents.only.for.physical.systems',
                    e.response.read())
            self.assertEquals(403, e.response.status)

        # Now list consumer's entitlements:
        result = self.cp.getEntitlements(virt_uuid)
        self.assertEquals(type([]), type(result))
        self.assertEquals(0, len(result))

    def test_list_entitlements_product_filtering(self):
        self.cp.bindProduct(self.uuid, 'virtualization_host')
        result = self.cp.getEntitlements(self.uuid)
        self.assertEquals(1, len(result))

        self.cp.bindProduct(self.uuid, 'monitoring')
        result = self.cp.getEntitlements(self.uuid)
        self.assertEquals(2, len(result))

        result = self.cp.getEntitlements(self.uuid, 
                product_id='monitoring')
        self.assertEquals(1, len(result))

    def test_bind_by_product(self):
        # Request a monitoring entitlement:
        results = self.cp.bindProduct(self.uuid, 'monitoring')
        for result in results:
            self.assertTrue('id' in result)
            self.assertEquals('monitoring', result['pool']['productId'])

        # Now list consumer's entitlements:
        result = self.cp.getEntitlements(self.uuid)
        print result

    def test_unbind_all_single(self):
        pools = self.cp.getPools(consumer=self.uuid)
        pool = pools[0]

        self.cp.bindPool(self.uuid, pool['id'])

        # Now unbind it
        self.cp.unBindAll(self.uuid)

        self.assertEqual([], self.cp.getEntitlements(self.uuid))

    def test_unbind_all_multi(self):
        pools = self.cp.getPools(consumer=self.uuid)

        preconsumed=0
        postconsumed=0

        if len(pools) > 1:
            for pool in pools:
                preconsumed = preconsumed + pool['consumed']
                self.cp.bindPool(self.uuid, pool['id'])

            pools = self.cp.getPools(consumer=self.uuid)
            for pool in pools:
                postconsumed = postconsumed + pool['consumed']
                    
            self.assertEqual(preconsumed+len(pools), postconsumed)

            # Unbind them all
            self.cp.unBindAll(self.uuid)
            self.assertEqual([], self.cp.getEntitlements(self.uuid))
            postunbound = 0
            pools = self.cp.getPools(consumer=self.uuid)
            for pool in pools:
                postunbound = postunbound + pool['consumed']
            self.assertEqual(preconsumed, postunbound)

    def test_list_pools(self):
        pools = self.cp.getPools(consumer=self.uuid, product="monitoring")
        self.assertEquals(1, len(pools))

    def test_list_pools_for_bad_objects(self):
        self.assertRaises(Exception, self.cp.getPools, consumer='blah')
        self.assertRaises(Exception, self.cp.getPools, owner='-1')

    def test_list_pools_for_bad_query_combo(self):
        # This isn't allowed, should give bad request.
        self.assertRaises(Exception, self.cp.getPools, consumer=self.uuid, owner=1)


    def test_unregister_consumer(self):

        ret = self.cp.registerConsumer("UnregMe", "samplepass", "some testsystem", {'arch':'i386', 'cpu':'intel'}, {'os':'linux', 'release':'6.0'})
        uuid = ret['uuid']
        pools = self.cp.getPools()

        preconsumed=0
        postconsumed=0

        if len(pools) > 1:
            for pool in self.cp.getPools():
                preconsumed = preconsumed + pool['consumed']
                self.cp.bindPool(uuid, pool['id'])

            self.cp.unRegisterConsumer( uuid)

            for pool in self.cp.getPools():
                postconsumed = postconsumed + pool['consumed']

            self.assertEquals(preconsumed, postconsumed)

    def test_register_by_uuid(self):
        uuid = "special-uuid"
        try:
            consumer = self.cp.rest.get("/consumers/%s" % uuid)
            self.assertEqual(uuid, consumer['consumer']['uuid'])
        except CandlepinException, e:
            self.assertEquals(404, e.response.status)
            consumer = self.cp.registerConsumer('jesusr', 'redhat', 'byuuid', uuid=uuid)
            self.assertEqual(uuid, consumer['uuid'])

        # try reregistering
        try:
            consumer = self.cp.registerConsumer('jesusr', 'redhat', 'byuuid', uuid=uuid)
        except CandlepinException, e:
            self.assertEquals(400, e.response.status)
