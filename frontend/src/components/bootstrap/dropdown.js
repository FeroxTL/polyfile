import m from "mithril";

const dropDownState = {};


document.addEventListener('click', function(e) {
  // closes all DropDowns and call m.render()
  let hasOpened = Object.values(dropDownState).some(elem => elem);
  if (!hasOpened || e.target.closest('.dropdown') != null) return;

  Object.keys(dropDownState).forEach(key => {
    dropDownState[key] = false;
  });
  m.redraw();
});


const NavDropDownDivider = {
  view: () => (m("hr.dropdown-divider"))
};


const NavDropDownItem = {
  view: (vnode) => (m("li", m(m.route.Link, {class: "dropdown-item", ...vnode.attrs}, vnode.children)))
};


const NavDropDownRawItem = {
  view: (vnode) => (m("li", m("span[role=button]", {class: "dropdown-item", ...vnode.attrs}, vnode.children)))
};


const NavDropDown = {
  oninit: (vnode) => {
    dropDownState[vnode.attrs.id] = false;
  },
  toggleShow: (vnode) => {
    dropDownState[vnode.attrs.id] = !dropDownState[vnode.attrs.id];
  },
  view: function (vnode) {
    let show = dropDownState[vnode.attrs.id];

    return (
      m("ul.navbar-nav ms-auto me-2 me-lg-2", {class: show ? "show" : null}, [
        m("li.nav-item dropdown", [
          m("a.nav-link dropdown-toggle[href=#]", {
              id: vnode.attrs.id,
              onclick: (e) => {
                this.toggleShow(vnode);
                e.preventDefault();
              }
            }, m("i.fas fa-user fa-fw")
          ),
          m("ul.dropdown-menu dropdown-menu-end",
            {
              "aria-labelledby": vnode.attrs.id,
              class: show ? "show" : null,
              "data-bs-popper": show ? "none" : null
            },
            vnode.children
          ),
        ])
      ])
    );
  }
};


const DropDown = {
  oninit: function(vnode) {
    this.id = vnode.attrs.id;
    dropDownState[this.id] = false;
  },
  toggleShow: function() {
    dropDownState[this.id] = !dropDownState[this.id];
  },
  view: function(vnode) {
    let show = dropDownState[this.id];

    return (
      m("div.dropdown", [
        m("a.btn btn-secondary[href=#]",
          {
            id: vnode.attrs.id,
            class: show ? "show" : null,
            onclick: (e) => {
              this.toggleShow(vnode);
              e.preventDefault();
            }
          },
          m("i.fa-solid fa-ellipsis")
        ),
        m("ul.dropdown-menu dropdown-menu-end",
          {
            "aria-labelledby": vnode.attrs.id,
            class: show ? "show" : null,
            "data-bs-popper": show ? "none" : null
          },
          vnode.children
        ),
      ])
    );
  }
};


export {
  dropDownState,
  NavDropDown,
  NavDropDownItem,
  NavDropDownDivider,
  DropDown,
  NavDropDownRawItem,
};