import m from "mithril";
import {getCookie} from "../../utils/cookie";
import {globalNodesData, Node} from "../../models/nodes";
import {modal} from "../../components/bootstrap/modal";
import {FormInput} from "../../components/bootstrap/form";


function showCreateDirectoryModal(lib_id, path) {
  path = path || "/";

  let nodeFormData = {
    instance: {
      name: "",
    },
    save: function () {
      return (
        m.request({
          method: "POST",
          url: "/api/v1/libraries/:lib_id/mkdir:path",
          params: {lib_id: lib_id, path: path},
          body: this.instance,
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
          }
        }).then((data) => {
          globalNodesData.addNode(new Node({library: globalNodesData.library, ...data}));
          return data;
        })
      )
    },
  };

  function formSubmit(e) {
    e.preventDefault();
    nodeFormData.save().then(() => {
      modal.close();
    });
  }

  let CreateDirectoryForm = {
    view: function () {
      return (
        m("form", {onsubmit: formSubmit}, [
          m("div.mb-3", [
            m(FormInput, {
              labelText: "Name",
              oninput: (e) => {
                nodeFormData.instance["name"] = e.target.value
              },
              value: nodeFormData.instance["name"],
            })
          ]),
        ])
      )
    }
  };

  let buttonOk = {
    view: () => (m("button.btn btn-primary[type=button]", {onclick: formSubmit}, "Create"))
  };

  modal.show({
    buttons: [modal.BtnCancel, buttonOk],
    title: "Create directory",
  }, CreateDirectoryForm)
}


function showRemoveNodeModal(node) {
  let nodeFormData = {
    save: function () {
      return (
        m.request({
          method: "DELETE",
          url: "/api/v1/libraries/:lib_id/rm:path",
          params: {lib_id: node.library.id, path: node.fullPath},
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
          }
        }).then((data) => {
          globalNodesData.removeNode(node);
          return data;
        })
      )
    },
  };

  function formSubmit(e) {
    e.preventDefault();
    nodeFormData.save().then(() => {
      modal.close();
    });
  }

  let RemoveNodeForm = {
    view: function () {
      return (
        m("p", `Are you sure you want to delete "${node.name}"?`)
      )
    }
  };

  let buttonOk = {
    view: () => (m("button.btn btn-danger[type=button]", {onclick: formSubmit}, "Remove"))
  };

  modal.show({
    buttons: [modal.BtnCancel, buttonOk],
    title: "Remove node",
  }, RemoveNodeForm)
}


function showNodeMenu(node) {
  let nodeFormData = {
    node: null,
    save: function() {
      return (
        m.request({
          method: "PUT",
          url: "/api/v1/libraries/:lib_id/rename:path...",
          params: {lib_id: node.library.id, path: node.fullPath},
          body: this.node,
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
          }
        })
      )
    }
  };

  function formSubmit(e) {
    e.preventDefault();
    nodeFormData.save().then((result) => {
      Object.assign(node, result);
      modal.close();
    });
  }

  let EditNodeForm = {
    oninit: () => {nodeFormData.node = Object.assign({}, node)},
    view: function() {
      return (
        m("form", {onsubmit: formSubmit}, [
          m("div.mb-3", [
            m(FormInput, {
              labelText: "Name",
              oninput: (e) => {nodeFormData.node["name"] = e.target.value},
              value: nodeFormData.node["name"],
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
    view: () => (m("button.btn btn-danger me-auto[type=button]", {onclick: () => {showRemoveNodeModal(node)}}, "Remove"))
  };

  modal.show({
    buttons: [buttonDelete, modal.BtnCancel, buttonOk],
    title: "Node settings",
  }, EditNodeForm)
}


export {showCreateDirectoryModal, showNodeMenu};
