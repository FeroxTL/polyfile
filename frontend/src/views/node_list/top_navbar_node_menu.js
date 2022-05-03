import m from "mithril";
import {getCookie} from "../../utils/cookie";
import {globalNodesData, Node} from "../../models/nodes";
import {showCreateDirectoryModal} from "./node_modals";


let TopNavBarNodeMenu = {
  showModal: function (e) {
    e.preventDefault();
    showCreateDirectoryModal(m.route.param("lib_id"), globalNodesData.currentPath)
  },
  uploadFile: function (e) {
    let file = e.target.files[0];
    const path = globalNodesData.currentPath;

    let body = new FormData();
    body.append("file", file);

    m.request({
      method: "POST",
      url: "/api/v1/lib/:lib_id/upload:path...",
      params: {
        lib_id: m.route.param("lib_id"),
        path: path,
      },
      body: body,
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      }
    }).then((data) => {
      globalNodesData.addNode(new Node({library: globalNodesData.library, path: path, ...data}));
      return data;
    })
  },
  view: function() {
    let disabled = globalNodesData.status !== "done";

    return [
      m(m.route.Link, {
        class: ["btn btn-secondary btn-sm me-1 ms-1", disabled ? "disabled" : null].join(" "),
        onclick: this.showModal,
        disabled: disabled,
      }, [
        m("i.fa-solid fa-plus"),
        m("span.d-none d-sm-inline ps-1", "Create directory"),
      ]),
      m("label.btn btn-secondary btn-sm me-1 ms-1", {
        class: disabled ? "disabled" : null,
      }, [
        m("input[type=file][hidden]", {onchange: this.uploadFile, disabled: disabled}),
        m("i.fa-solid fa-cloud-arrow-up"),
        m("span.d-none d-sm-inline ps-1", "Upload file"),
      ]),
    ]
  }
};

export default TopNavBarNodeMenu;
