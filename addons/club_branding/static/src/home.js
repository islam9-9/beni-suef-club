/** @odoo-module **/
import { Component } from '@odoo/owl';
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';

class ClubHome extends Component {
    static template = 'club_branding.Home';
    static props = ['*'];
    setup() { this.apps = useService('app_menu'); }
    get groups() {
        const groups = [
            {name: 'الأعضاء والتواصل', key: 'people', apps: []},
            {name: 'المالية والتشغيل', key: 'operations', apps: []},
            {name: 'الإدارة والإعدادات', key: 'admin', apps: []},
        ];
        for (const app of this.apps.getAppsMenuItems()) {
            if (app.xmlid === 'club_branding.menu_club_home') continue;
            const module = (app.xmlid || '').split('.')[0];
            const index = ['mail', 'membership', 'contacts', 'calendar'].includes(module) ? 0
                : ['account', 'purchase', 'stock', 'sale', 'sale_management'].includes(module) ? 1 : 2;
            groups[index].apps.push(app);
        }
        return groups.filter(group => group.apps.length);
    }
    open(app) { return this.apps.selectApp(app); }
}
registry.category('actions').add('club_branding.home', ClubHome);
