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
package org.fedoraproject.candlepin.pinsetter.tasks;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.fail;
import static org.mockito.Matchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.*;

import org.fedoraproject.candlepin.audit.Event;
import org.fedoraproject.candlepin.audit.EventFactory;
import org.fedoraproject.candlepin.audit.EventSink;
import org.fedoraproject.candlepin.controller.Entitler;
import org.fedoraproject.candlepin.controller.PoolManager;
import org.fedoraproject.candlepin.exceptions.BadRequestException;
import org.fedoraproject.candlepin.exceptions.ForbiddenException;
import org.fedoraproject.candlepin.model.Consumer;
import org.fedoraproject.candlepin.model.Entitlement;
import org.fedoraproject.candlepin.model.Pool;
import org.fedoraproject.candlepin.policy.EntitlementRefusedException;
import org.fedoraproject.candlepin.policy.ValidationError;
import org.fedoraproject.candlepin.policy.ValidationResult;

import org.junit.Before;
import org.junit.Test;
import org.xnap.commons.i18n.I18n;
import org.xnap.commons.i18n.I18nFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
/**
 * EntitlerTest
 */
public class EntitlerTest {
    private PoolManager pm;
    private EventFactory ef;
    private EventSink sink;
    private I18n i18n;
    private Entitler entitler;
    private Consumer consumer;

    private ValidationResult fakeOutResult(String msg) {
        ValidationResult result = new ValidationResult();
        ValidationError err = new ValidationError(msg);
        result.addError(err);
        return result;
    }

    @Before
    public void init() {
        pm = mock(PoolManager.class);
        ef = mock(EventFactory.class);
        sink = mock(EventSink.class);
        consumer = mock(Consumer.class);
        i18n = I18nFactory.getI18n(
            getClass(),
            Locale.US,
            I18nFactory.READ_PROPERTIES | I18nFactory.FALLBACK
        );
        entitler = new Entitler(pm, i18n, ef, sink);
    }

    @Test
    public void bindByPool() throws EntitlementRefusedException {
        String poolid = "pool10";
        Pool pool = mock(Pool.class);
        Entitlement ent = mock(Entitlement.class);

        when(pm.find(eq(poolid))).thenReturn(pool);
        when(pm.entitleByPool(eq(consumer), eq(pool), eq(1))).thenReturn(ent);

        List<Entitlement> ents = entitler.bindByPool(poolid, consumer, 1);
        assertNotNull(ents);
        assertEquals(ent, ents.get(0));
    }

    @Test(expected = BadRequestException.class)
    public void nullPool() {
        String poolid = "foo";
        when(pm.find(eq(poolid))).thenReturn(null);
        entitler.bindByPool(poolid, null, 10);
    }

    @Test(expected = ForbiddenException.class)
    public void someOtherErrorPool() {
        bindByPoolErrorTest("do.not.match");
    }

    @Test(expected = ForbiddenException.class)
    public void consumerTypeMismatchPool() {
        bindByPoolErrorTest("rulefailed.consumer.type.mismatch");
    }

    @Test(expected = ForbiddenException.class)
    public void alreadyHasProductPool() {
        bindByPoolErrorTest("rulefailed.consumer.already.has.product");
    }

    @Test(expected = ForbiddenException.class)
    public void noEntitlementsAvailable() {
        bindByPoolErrorTest("rulefailed.no.entitlements.available");
    }

    private void bindByPoolErrorTest(String msg) {
        try {
            String poolid = "pool10";
            Pool pool = mock(Pool.class);
            EntitlementRefusedException ere = new EntitlementRefusedException(
                fakeOutResult(msg));

            when(pool.getId()).thenReturn(poolid);
            when(pm.find(eq(poolid))).thenReturn(pool);
            when(pm.entitleByPool(eq(consumer), eq(pool), eq(1))).thenThrow(ere);
            entitler.bindByPool(poolid, consumer, 1);
        }
        catch (EntitlementRefusedException e) {
            fail(msg + ": threw unexpected error");
        }
    }

    @Test(expected = ForbiddenException.class)
    public void alreadyHasProduct() throws EntitlementRefusedException {
        bindByProductErrorTest("rulefailed.consumer.already.has.product");
    }

    @Test(expected = ForbiddenException.class)
    public void noEntitlementsForProduct() throws EntitlementRefusedException {
        bindByProductErrorTest("rulefailed.no.entitlements.available");
    }

    @Test(expected = ForbiddenException.class)
    public void mismatchByProduct() throws EntitlementRefusedException {
        bindByProductErrorTest("rulefailed.consumer.type.mismatch");
    }

    @Test(expected = ForbiddenException.class)
    public void virtOnly() throws EntitlementRefusedException {
        bindByProductErrorTest("rulefailed.virt.only");
    }

    @Test(expected = ForbiddenException.class)
    public void allOtherErrors() {
        bindByProductErrorTest("generic.error");
    }

    private void bindByProductErrorTest(String msg) {
        try {
            String[] pids = {"prod1", "prod2", "prod3"};
            EntitlementRefusedException ere = new EntitlementRefusedException(
                fakeOutResult(msg));
            when(pm.entitleByProducts(eq(consumer), eq(pids), eq(1))).thenThrow(ere);
            entitler.bindByProducts(pids, consumer, 1);
        }
        catch (EntitlementRefusedException e) {
            fail(msg + ": threw unexpected error");
        }
    }

    @Test
    public void events() {
        List<Entitlement> ents = new ArrayList<Entitlement>();
        ents.add(mock(Entitlement.class));
        ents.add(mock(Entitlement.class));

        Event evt1 = mock(Event.class);
        Event evt2 = mock(Event.class);
        when(ef.entitlementCreated(any(Entitlement.class)))
            .thenReturn(evt1)
            .thenReturn(evt2);
        entitler.sendEvents(ents);

        verify(sink).sendEvent(eq(evt1));
        verify(sink).sendEvent(eq(evt2));
    }

    @Test
    public void noEventsWhenEntitlementsNull() {
        entitler.sendEvents(null);
        verify(sink, never()).sendEvent(any(Event.class));
    }

    @Test
    public void noEventsWhenListEmpty() {
        List<Entitlement> ents = new ArrayList<Entitlement>();
        entitler.sendEvents(ents);
        verify(sink, never()).sendEvent(any(Event.class));
    }
}