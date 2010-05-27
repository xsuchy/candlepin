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
package org.fedoraproject.candlepin.audit;

import org.apache.log4j.Logger;
import org.fedoraproject.candlepin.model.EventCurator;

import com.google.inject.Inject;

/**
 * DatabaseListener
 */
public class DatabaseListener implements EventListener {

    private EventCurator eventCurator;
    private static Logger log = Logger.getLogger(DatabaseListener.class);

    @Inject
    public DatabaseListener(EventCurator eventCurator) {
        this.eventCurator = eventCurator;
    }

    @Override
    public void onEvent(Event event) {
        log.debug("Received event: " + event);
        eventCurator.create(event);
    }

}