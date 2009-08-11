/**
 * Copyright (c) 2008 Red Hat, Inc.
 *
 * This software is licensed to you under the GNU General Public License,
 * version 2 (GPLv2). There is NO WARRANTY for this software, express or
 * implied, including the implied warranties of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
 * along with this software; if not, see
 * http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
 *
 * Red Hat trademarks are not licensed under GPLv2. No permission is
 * granted to use or replicate Red Hat trademarks that are incorporated
 * in this software or its documentation.
 */
package org.fedoraproject.candlepin.api;

import org.apache.log4j.Logger;

import org.fedoraproject.candlepin.model.Consumer;
import org.fedoraproject.candlepin.model.ConsumerType;
import org.fedoraproject.candlepin.model.ObjectFactory;
import org.fedoraproject.candlepin.model.Product;
import org.fedoraproject.candlepin.model.ProductFactory;

import java.util.List;

/** 
 * EntitlementMatcher - initial class for matching products compatability with 
 * an entitlement.
 * @version $Rev$
 */
public class EntitlementMatcher {

    /**
     * Logger for this class
     */
    private static final Logger log = Logger
            .getLogger(EntitlementMatcher.class);
    
    
    /**
     * Check if a given consumer is compat with given product.
     * @param consumer to check 
     * @param product to check
     * @return boolean if compat or not
     */
    public boolean isCompatible(Consumer c, Product p) {
        log.debug("isCompatible() : Consuner: " + c  + " product: " + p);
        if (c.getType() == null) {
            throw new NullPointerException("Consumer has no type.");
        }
        List f = ObjectFactory.get().listObjectsByClass(ConsumerType.class);
        List<ConsumerType> types = ProductFactory.get().getCompatibleConsumerTypes(p);
        
        return (types != null && types.contains(c.getType())); 
    }

}
