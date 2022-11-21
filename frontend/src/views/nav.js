import m from "mithril";
import {NavDropDown, NavDropDownDivider, NavDropDownItem, NavDropDownRawItem} from "../components/bootstrap/dropdown";
import Auth from "../models/auth";
import routes from "../utils/routes";
import {modal} from "../components/bootstrap/modal";


function onToggleSideNav(value, e) {
  const className = "sb-sidenav-toggled";

  if (value === document.body.classList.contains(className)) {
    e.redraw = false;
    return;
  }

  document.body.classList.toggle(className, value);
}


function showLogoutModal() {
  function formSubmit(e) {
    e.preventDefault();
    Auth.logout().then((response) => {
      document.location.href = response["next_url"] || "/";
    });
  }


  let buttonOk = {
    view: () => (m("button.btn btn-primary[type=button]", {onclick: formSubmit}, "Logout"))
  };

  modal.show({
    buttons: [modal.BtnCancel, buttonOk],
    title: "Logout",
  })
}


let TopNav = {
  view: function(vnode) {
    const {topNavBarComponent} = vnode.attrs;

    return (
      m("nav.sb-topnav navbar navbar-expand navbar-dark bg-dark", [
        m("a.navbar-brand ps-3 d-none d-sm-inline", {href: "#"}, "Polyfile"),
        m(
          "button#sidebarToggle.btn btn-link btn-sm order-1 order-lg-0 me-1 me-lg-0",
          {onclick: onToggleSideNav.bind(null, undefined)},
          m("i.fas fa-bars")
        ),
        topNavBarComponent && m(topNavBarComponent, vnode.attrs),
        m(NavDropDown, {id: 'navMenuDropDown'}, [
          m(NavDropDownItem, {href: routes.settings}, "Settings"),
          m(NavDropDownDivider),
          m(NavDropDownRawItem, {
            onclick: () => {showLogoutModal()}
          }, "Logout"),
        ]),
      ])
    )
  }
};


let SideNavAccordion = {
  view: function (vnode) {
    const {sideNavThemeClass="sb-sidenav-dark"} = vnode.attrs;

    return (
      m("nav#sidenavAccordion.sb-sidenav accordion", {class: sideNavThemeClass}, [
        m("div.sb-sidenav-menu", [
          m("div.nav", vnode.children)
        ]),
        m("div.sb-sidenav-footer", Auth.currentUser && [
          m("div.small", "Logged in as:"),
          Auth.currentUser.fullName
        ])
      ])
    );
  }
};


const SideHeading = {
  view: function(vnode) {
    return m("div.sb-sidenav-menu-heading", vnode.children);
  }
};


const SideLink = {
  view: function(vnode) {
    const {iconClass, href=""} = vnode.attrs;

    return (
      m(m.route.Link, {href: href, class: "nav-link"}, [
        iconClass && m("div.sb-nav-link-icon", m("i", {class: iconClass})),
        vnode.children
      ])
    );
  }
};


let SideNavView = {
  oninit: () => {
    document.body.className = 'sb-nav-fixed';
  },

  view: (vnode) => {
    const {sideMenuItems=[]} = vnode.attrs;

    return (
      m("main", [
        m(TopNav, vnode.attrs),
        m("div#layoutSidenav", [
          m("div#layoutSidenav_nav", m(SideNavAccordion, vnode.attrs, sideMenuItems)),
          m(
            "div#layoutSidenav_content",
            {onclick: onToggleSideNav.bind(null, false)},
            m("div.container-fluid px-4", vnode.children),
          )
        ]),
        modal.renderBackdrop(),
      ])
    )
  }
};

export {
  SideNavView,
  SideHeading,
  SideLink,
};
