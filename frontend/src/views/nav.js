import m from "mithril";
import {NavDropDown, NavDropDownItem} from "../components/bootstrap/dropdown";
import {Auth} from "../models/auth";
import routes from "../utils/routes";
import {modal} from "../components/bootstrap/modal";


function toggleSideNav(value) {
  document.body.classList.toggle('sb-sidenav-toggled', value);
}


let TopNav = {
  view: function(vnode) {
    const {topNavBarComponent} = vnode.attrs;

    return (
      m("nav.sb-topnav navbar navbar-expand navbar-dark bg-dark", [
        m("a.navbar-brand ps-3 d-none d-sm-inline", {href: "#"}, "Polyfile"),
        m(
          "button#sidebarToggle.btn btn-link btn-sm order-1 order-lg-0 me-1 me-lg-0[href=#]",
          {
            onclick: () => {
              toggleSideNav()
            }
          },
          m("i.fas fa-bars")
        ),
        topNavBarComponent && m(topNavBarComponent, vnode.attrs),
        m(NavDropDown, {id: 'navMenuDropDown'}, [
          // m(NavDropDownItem, "Settings"),
          // m(NavDropDownDivider),
          m(NavDropDownItem, {
            onclick: () => {
              Auth.logout().then((response) => {
                document.location.href = response["next_url"] || "/";
              })
            }
          }, "Logout"),
        ]),
      ])
    )
  }
};


let SideNavAccordion = {
  view: function () {
    return (
      m("nav#sidenavAccordion.sb-sidenav accordion sb-sidenav-dark", [
        m("div.sb-sidenav-menu", [
          m("div.nav", [
            m("div.sb-sidenav-menu-heading", "Files"),
            m(m.route.Link, {href: routes.library_index, class: "nav-link"}, [
              m("div.sb-nav-link-icon", m("i.fa-solid fa-box")),
              "My libraries",
            ]),
          ])
        ]),
        m("div.sb-sidenav-footer", [
          m("div.small", "Logged in as:"),
          "Start Bootstrap"
        ])
      ])
    );
  }
};


let SideNavView = {
  oninit: () => {
    document.body.className = 'sb-nav-fixed';
  },

  view: (vnode) => {
    return (
      m("main", [
        m(TopNav, vnode.attrs),
        m("div#layoutSidenav", [
          m("div#layoutSidenav_nav", m(SideNavAccordion)),
          m(
            "div#layoutSidenav_content",
            {
              onclick: () => {
                toggleSideNav(false)
              }
            },
            m("div.container-fluid px-4", vnode.children),
          )
        ]),
        modal.renderBackdrop(),
      ])
    )
  }
};

export {SideNavView};
