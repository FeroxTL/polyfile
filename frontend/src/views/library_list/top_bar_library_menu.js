import m from "mithril";
import {FormInput} from "../../components/bootstrap/form";
import {modal} from "../../components/bootstrap/modal";
import {getCookie} from "../../utils/cookie";
import {globalLibraryData, Library} from "../../models/library";


function showCreateLibraryModal() {
  let libraryFormData = {
    library: new Library({}),
    save: function() {
      return (
        m.request({
          method: "POST",
          url: "/api/v1/lib",
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
  view: function () {
    return [
      m("a.btn btn-secondary btn-sm me-1 ms-2[href=#]", {
        onclick: () => {
          showCreateLibraryModal()
        }
      }, [
        m("i.fa-solid fa-plus"),
        m("span.d-none d-sm-inline ps-1", "Create library"),
      ]),
    ]
  }
};


export default TopNavBarLibraryMenu;