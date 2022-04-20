import m from "mithril";
import {globalLibraryData, Library} from "../models/library";
import routes from "../utils/routes";
import {SideNavView} from "./nav";
import {Loader} from "../components/bootstrap/loader";
import {modal} from "../components/bootstrap/modal";
import {getCookie} from "../utils/cookie";
import {FormInput} from "../components/bootstrap/form";


function navigateLibrary(library) {
  m.route.set(routes.library_nodes_path, {lib_id: library.id, path: "/"});
}


function showSubmitRemoveModal(library) {
  let Content = {
    view: function() {
      return m("span", `Remove library "${library.name}"?`)
    }
  };

  function formSubmit() {
    console.log('submit remove', library);
    //todo remove library api is not implemented
    alert('this function is not implemented yet');
    modal.close();
  }

  let buttonDelete = {
    view: function() {
      return m("button.btn btn-danger[type=button]", {onclick: formSubmit}, "Remove")
    }
  };

  modal.show({buttons: [modal.BtnCancel, buttonDelete], title: "Remove library"}, Content)
}


function showLibraryMenu(library) {
  let libraryFormData = {
    library: null,
    save: function() {
      return (
        m.request({
          method: "PUT",
          url: "/api/v1/libraries/:lib_id",
          params: {lib_id: library.id},
          body: this.library,
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
          }
        })
      )
    }
  };

  function formSubmit(e) {
    e.preventDefault();
    libraryFormData.save().then((result) => {
      Object.assign(library, result);
      modal.close();
    });
  }

  let EditLibraryForm = {
    oninit: () => {libraryFormData.library = Object.assign({}, library)},
    view: function() {
      return (
        m("form", {onsubmit: formSubmit}, [
          m("div.mb-3", [
            m(FormInput, {
              labelText: "Name",
              oninput: (e) => {libraryFormData.library["name"] = e.target.value},
              value: libraryFormData.library["name"],
            })
          ]),
        ])
      )
    }
  };

  let buttonOk = {
    view: () => (m("button.btn btn-primary[type=button]", {onclick: formSubmit}, "Submit"))
  };

  let buttonDelete = {
    view: () => (m("button.btn btn-danger me-auto[type=button]", {onclick: () => {showSubmitRemoveModal(library)}}, "Remove"))
  };

  modal.show({
    buttons: [buttonDelete, modal.BtnCancel, buttonOk],
    title: "Library settings",
  }, EditLibraryForm)
}


let LibraryList = {
  view: () => (
    m("table.table table-hover", [
      m("thead",
        m("tr", [
          m("th.col-1 p-0[scope=col]"),
          m("th.col p-0[scope=col]", "Name"),
          m("th.col-1 p-0[scope=col]", "Options"),
        ])
      ),
      m("tbody", globalLibraryData.list.map((library) => (
        m("tr", [
          m("td.align-middle text-center[role=button]", {onclick: () => {navigateLibrary(library)}}, m("i.fa-solid fa-box text-secondary h3")),
          m("td[role=button]", {onclick: () => {navigateLibrary(library)}}, [
            m("b", library.name),
            // m("br"),
            // m("span", "Bottom text"),
          ]),
          m("td.align-middle text-center",
            m("a.btn btn-secondary[href=#]", {onclick: () => {showLibraryMenu(library)}}, m("i.fa-solid fa-ellipsis-vertical"))
          )
        ])
      ))),
    ])
  )
};


function showCreateLibraryModal() {
  let libraryFormData = {
    library: new Library({}),
    save: function() {
      return (
        m.request({
          method: "POST",
          url: "/api/v1/libraries",
          body: this.library,
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
          }
        }).then((data) => {
          globalLibraryData.addLibrary(new Library(data));
          return data;
        })
      )
    }
  };

  function formSubmit(e) {
    e.preventDefault();
    libraryFormData.save().then(() => {
      modal.close();
    });
  }

  let CreateLibraryForm = {
    view: function() {
      return (
        m("form", {onsubmit: formSubmit}, [
          m("div.mb-3", [
            m(FormInput, {
              labelText: "Name",
              oninput: (e) => {libraryFormData.library["name"] = e.target.value},
              value: libraryFormData.library["name"],
            })
          ]),
          m("div.mb-3", [
            m(FormInput, {
              labelText: "Data source",
              oninput: (e) => {libraryFormData.library["data_source"] = e.target.value},
              value: libraryFormData.library["data_source"],
            })
          ]),
        ])
      )
    }
  };

  let buttonOk = {
    view: () => (m("button.btn btn-primary[type=button]", {onclick: formSubmit}, "Submit"))
  };

  modal.show({
    buttons: [modal.BtnCancel, buttonOk],
    title: "Create library",
  }, CreateLibraryForm)
}


let TopNavBarLibraryMenu = {
  view: function() {
    return [
      m("a.btn btn-secondary btn-sm me-1 ms-2[href=#]", {onclick: () => {showCreateLibraryModal()}}, [
        m("i.fa-solid fa-plus"),
        m("span.d-none d-sm-inline ps-1", "Create library"),
      ]),
    ]
  }
};


let LibraryListView = {
  oninit: () => (globalLibraryData.fetch()),
  view: function() {
    return m(SideNavView, {
      topNavBarComponent: TopNavBarLibraryMenu,
    }, [
      globalLibraryData.status === "done" ? m(LibraryList) : m(Loader),
      modal.renderModal(),
    ])
  }
};


export default LibraryListView;
