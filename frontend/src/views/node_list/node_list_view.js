import {globalNodesData} from "../../models/nodes";
import m from "mithril";
import routes from "../../utils/routes";
import {showNodeMenu} from "./node_modals";
import showImageViewer from "../../components/image_viewer";


let NodeItem = {
  view: function(vnode) {
    let {node, attributes=[]} = vnode.attrs;

    return (
      m(".d-table", [
        m("div.d-table-cell align-middle text-center", m("i.fa-solid fa-box text-secondary h3")),
        m("div.d-table-cell ps-2", [
          m("b.text-break", node.name),
          attributes.map((attr) => ([
            m("br"),
            m("span", attr),
          ]))
        ])
      ])
    )
  }
};


let RowDirectoryItem = {
  onShowMenuClick: function(node, e) {
    e.preventDefault();
    showNodeMenu(node);
  },

  view: function(vnode) {
    let {node} = vnode.attrs;

    return (
      m("tr", [
        m("td[role=button]", {
          onclick: () => {
            let path = m.buildPathname(routes.library_nodes_path, {
              lib_id: node.library.id,
              path: node.fullPath,
            });
            m.route.set(path);
          }}, m(NodeItem, vnode.attrs)),
        m("td.align-middle text-center",
          m("a.btn btn-secondary", {onclick: this.onShowMenuClick.bind(null, node)}, m("i.fa-solid fa-ellipsis")),
        )
      ])
    )
  }
};


let RowFileItem = {
  onShowMenuClick: function(node, e) {
    e.preventDefault();
    showNodeMenu(node);
  },
  isImage: function(file) {
    return file.mimetype && file.mimetype.startsWith('image/') || false;
  },
  getImageList: function(nodeList) {
    return nodeList.filter(this.isImage)
  },

  onClickAction: function(node, e) {
    e.preventDefault();
    showImageViewer({currentNode: node, nodeList: this.getImageList(globalNodesData.list)});
  },

  view: function(vnode) {
    let {node} = vnode.attrs;

    return (
      m("tr", [
        m("td[role=button]", {onclick: this.onClickAction.bind(this, node)}, m(NodeItem, {
          node: node,
          attributes: [`${node.size} bytes`]
        })),
        m("td.align-middle text-center",
          m("a.btn btn-secondary", {onclick: this.onShowMenuClick.bind(null, node)}, m("i.fa-solid fa-ellipsis")),
        )
      ])
    );
  }
};


let RowItem = {
  view: function(vnode) {
    let {node} = vnode.attrs;

    return (
      node.isDirectory ?
        m(RowDirectoryItem, vnode.attrs) :
        m(RowFileItem, vnode.attrs))
  }
};


let NodeListView = {
  view: function () {
    const nodes = globalNodesData.list;

    if (!nodes.length) {
      return m("div.alert.alert-secondary", "No files");
    }

    return (
      m("table.table.mb-20", {class: nodes.length ? "table-hover" : null}, [
        m("thead",
          m("tr", [
            m("th.col p-0[scope=col]", "Name"),
            m("th.col-1 p-0[scope=col]", "Options"),
          ])
        ),
        m("tbody", nodes.map((item) => (m(RowItem, {node: item})))),
      ])
    )
  }
};

export default NodeListView;
