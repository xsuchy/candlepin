/**
 * Copyright (c) 2009 Red Hat, Inc.
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
package org.fedoraproject.candlepin.guice;

import com.google.inject.Inject;
import com.google.inject.Provider;
import org.fedoraproject.candlepin.auth.Principal;
import org.fedoraproject.candlepin.auth.UserPrincipal;
import org.fedoraproject.candlepin.model.Owner;
import org.fedoraproject.candlepin.model.OwnerCurator;

/**
 *
 */
public class TestPrincipalProvider implements Provider<Principal> {

    private static final String OWNER_NAME = "Default-Owner";

    private OwnerCurator ownerCurator;

    @Inject
    public TestPrincipalProvider(OwnerCurator ownerCurator) {
        this.ownerCurator = ownerCurator;
    }

    @Override
    public Principal get() {
        TestPrincipalProviderSetter principalSingleton = TestPrincipalProviderSetter.get();
        Principal principal = principalSingleton.getPrincipal();
        if (principal == null) {
            
            Owner owner = ownerCurator.lookupByKey(OWNER_NAME);

            if (owner == null) {
                owner = new Owner(OWNER_NAME);
                ownerCurator.create(owner);
            }
            principal = new UserPrincipal("Default User", owner, null);
        }   
        return principal;
    }

}