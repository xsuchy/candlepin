import httplib
import urllib
import urllib2
import sys
import simplejson as json
import os
import base64

class CandlepinException(Exception):
    def __init__(self, message, response):
        Exception.__init__(self, message)
        self.response = response

class Rest(object):
    def __init__(self, hostname="localhost", port="8080", api_url="/candlepin", cert_file=None, key_file=None, debug=None):
        self.hostname = hostname
        self.port = port
        self.api_url = api_url
        self.baseurl = "http://%s:%s/%s" % (self.hostname, self.port, self.api_url)
        self.json_headers = {"Content-type":"application/json",
                             "Accept": "application/json"}
        self.text_headers = {"Content-type":"text/plain",
                             "Accept": "text/plain"}

        self.headers = {"json": self.json_headers,
                        "text": self.text_headers}

        self.cert_file = cert_file
        self.key_file = key_file
        self.debug = debug

        # default content type
        self.content_type = None

    def _request(self, http_type, path, data=None, content_type=None, username=None, password=None):
        if content_type is None and self.content_type:
            content_type = self.content_type

        if self.port.find("443") >= 0:
            conn = httplib.HTTPSConnection(self.hostname, self.port, key_file = self.key_file, cert_file = self.cert_file)
        else:
            conn = httplib.HTTPConnection(self.hostname, self.port)

        if self.debug:
            conn.set_debuglevel(self.debug)
        url_path = "%s%s" % (self.api_url, path)
        full_url = "%s:%s%s" % (self.hostname, self.port, self.api_url)
        if self.debug:
            print "url: %s" % full_url
        
        headers = self.headers[content_type]
        #add Authorization header for basic auth
        if username != None:
            headers.update({"Authorization":"Basic %s" % base64.encodestring('%s:%s' % (username, password))[:-1]})

        conn.request(http_type, url_path, body=self.marshal(data, content_type),
                headers=headers)
        response = conn.getresponse()
        if response.status not in  [200, 204]:
            raise CandlepinException("%s - %s" % (response.status, response.reason),
                    response)

        rsp = response.read()
        
        if self.debug:
            print "response status: %s" % response.status
            print "response reason: %s" % response.reason

        if self.debug and self.debug >2:
            print "output: %s" % rsp

        if rsp != "":
            return self.demarshal(rsp, content_type)
        return None

    def get(self, path, content_type="json"):
        return self._request("GET", path, content_type=content_type)

    def head(self, path, content_type="json"):
        return self._request("HEAD", path, content_type=content_type)

    def post(self, path, data="", content_type="json", username=None, password=None):
        return self._request("POST", path, data=data, content_type=content_type, username=username, password=password)

    def put(self, path, data="", content_type="json"):
        return self._request("PUT", path, data=data, content_type=content_type)

    def delete(self, path, content_type="json"):
        return self._request("DELETE", path, content_type=content_type)

    def marshal(self,data, format):
        if format == "json":
            return json.dumps(data)
        return data

    def demarshal(self, data, format):
        if format == "json":
            return json.loads(data)
        return data

class CandlePinApi:
    def __init__(self, hostname="localhost", port="8080", api_url="/candlepin", cert_file=None, key_file=None, debug=None):
        self.rest = Rest(hostname=hostname, port=port, api_url=api_url, cert_file=cert_file, key_file=key_file, debug=debug)

    def registerConsumer(self, userid, password, name, hardware=None, 
            products=None, consumer_type="system", uuid=None):
        path = "/consumers"

        # Don't think this is used yet, and definitely shouldn't
        # be going into the entrys map:
        #if products is not None:
        #    for key in products:
        #        entrys.append({'key':key,
        #                       'value':products[key]})
                              
        consumer = {"consumer": {
                    "type": {'label': consumer_type},
                    "name": name,
                    "facts": {
                       "metadata": hardware
                    }
            }
        }

        if uuid:
            consumer['consumer']['uuid'] = uuid

        blob = self.rest.post(path, data=consumer, username=userid, password=password)
        return blob['consumer']

    def unRegisterConsumer(self,consumer_uuid):
        path = "/consumers/%s" % consumer_uuid
        print path
        blob = self.rest.delete(path)
        return blob

    def bindProduct(self, consumer_uuid, product_label):
        path = "/consumers/%s/entitlements?product=%s" % (consumer_uuid, product_label)
        blobs = []
        for entitlement in self.rest.post(path):
            blobs.append(entitlement['entitlement'])

        return blobs

    def bindPool(self, consumer_uuid, pool_id):
        path = "/consumers/%s/entitlements?pool=%s" % (consumer_uuid, pool_id)
        blobs = []
        for entitlement in self.rest.post(path):
            blobs.append(entitlement['entitlement'])
        return blobs

    def bindRegToken(self, consumer_uuid, regtoken):
        path = "/consumers/%s/entitlements?token=%s" % (consumer_uuid, regtoken)
        blobs = []
        for entitlement in self.rest.post(path):
            blobs.append(entitlement['entitlement'])
        return blobs

    def unBindAll(self, consumer_uuid):
        path = "/consumers/%s/entitlements" % consumer_uuid
        blob = self.rest.delete(path)
        return blob

    def unBindEntitlement(self,  entitlementId):
        path = "/entitlements/%s" % (entitlementId)
        blob = self.rest.delete(path)
        return blob

    def unBindBySerialNumbers(self, consumer_uuid, serial_number_list):
        path = "/entitlements/consumer/%s/%s" % (consumer_uuid, ','.join(serial_number_list))
        blob = self.rest.delete(path)
        return blob

    def getCertificates(self, consumer_uuid, serials = []):
        """
        Fetch a consumers entitlement certificates, with an optional list
        of serial numbers to filter on.
        """
        serial_filter = ""
        str_serials = []
        for s in serials:
            str_serials.append(str(s))
        if len(str_serials) > 0:
            serial_filter = "?serials=" + ",".join(str_serials)
        path = "/consumers/%s/certificates%s" % (consumer_uuid, serial_filter)
        print "getCertificates = %s" % path
        print self.rest.get(path)
        return [c['cert'] for c in self.rest.get(path)]

    def getCertificateSerials(self, consumer_uuid):
        path = "/consumers/%s/certificates/serials" % consumer_uuid
        return self.rest.get(path)

    def getPool(self, poolId):
         path = "/pools/%s" % poolId
         return self.rest.get(path)

    def getPools(self, consumer=None, owner=None, product=None):
        """
        Limit available entitlement pools.
          consumer - Limit to pools available to given UUID.
          owner - Limit pools to the given owner ID.
          product - Limit pools to the given product ID.
        """
        path = "/pools?"
        if consumer:
            path = "%sconsumer=%s&" % (path, consumer)
        if owner:
            path = "%sowner=%s&" % (path, owner)
        if product:
            path = "%sproduct=%s&" % (path, product)
        return [p['pool'] for p in self.rest.get(path)]

    def getEntitlements(self, consumer_uuid, product_id=None):
        path = "/consumers/%s/entitlements" % consumer_uuid
        if product_id:
            path = "%s?product=%s" % (path, product_id)
        return self.rest.get(path)

    def getProducts(self):
        path = "/products/"
        return [p['product'] for p in self.rest.get(path)]

    def getSubscriptions(self):
        path = "/subscriptions/"
        subs = self.rest.get(path);
        return subs

    def createSubscription(self, subData):
        path = "/subscriptions/"
        subs = self.rest.post(path, data=subData);
        return subs

    def deleteSubscription(self, subId):
        path = "/subscriptions/%s" % subId
        return self.rest.delete(path)

    def uploadRules(self, rules_text):
        path = "/rules/"
        encoded = base64.b64encode(rules_text)
        return self.rest.post(path, data=encoded)



if __name__ == "__main__":

    cp = CandlePinApi(hostname="localhost", port="8080", api_url="/candlepin", debug=10)
    ret = cp.registerConsumer("whoever", "doesntmatter", "some system", {'arch':'i386', 'cpu':'intel'}, {'os':'linux', 'release':'4.2'})
    print ret
    print cp.unRegisterConsumer("dontuser", "notreallyapassword", ret['uuid'])

    ret =  cp.registerConsumer("whoever", "doesntmatter", "some system", {'arch':'i386', 'cpu':'intel'}, {'os':'linux', 'release':'4.2'})

    # broken atm
    print cp.bindProduct(ret['uuid'], "monitoring")

    uuid = ret['uuid']
    ret = cp.syncCertificates(uuid, [])
    print ret

#    ret = cp.unBindAll(uuid)
#    print ret

    ret = cp.getEntitlementPools(uuid)
    print ret

    ret = cp.unBindAll(uuid)
    print ret
