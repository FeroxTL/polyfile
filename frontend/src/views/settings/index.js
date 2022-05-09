import m from "mithril";
import {SideHeading, SideLink, SideNavView} from "../nav";
import {modal} from "../../components/bootstrap/modal";
import PersonalSettingsView from "./personal";
import UsersSettingsView from "./users";
import routes from "../../utils/routes";
import Auth from "../../models/auth";
import DataSourceView from "./data_source";


function getMapping() {
  const mapping = {
    personal: PersonalSettingsView,
  };

  if (Auth.currentUser.isSuperuser) {
    Object.assign(mapping, {
      users: UsersSettingsView,
      data_source: DataSourceView,
    })
  }

  return mapping;
}


const SettingsWrapperView = {
  oninit: function() {
    this.mapping = getMapping();
  },

  getMenuItems: function() {
    const menuItems = Object.entries(this.mapping).map(([key, view]) => (
      m(SideLink, {
        href: m.buildPathname(routes.settings_detail, {"key": key}),
        iconClass: view.iconClass || "fa-solid fa-question"
      }, view.verboseName || key)
    ));

    return [
      m(SideHeading, 'Settings'),
      ...menuItems,
    ]
  },

  view: function(vnode) {
    const {key} = vnode.attrs;
    const childView = this.mapping[key];

    if (childView === undefined) {
      return m.route.set(routes.settings, null, {replace: true});
    }

    return [
      m(SideNavView, {sideMenuItems: this.getMenuItems(), sideNavThemeClass: "sb-sidenav-light"},
        m(childView, vnode.attrs),
      ),
      modal.renderModal(),
    ]
  }
};


export {SettingsWrapperView};
