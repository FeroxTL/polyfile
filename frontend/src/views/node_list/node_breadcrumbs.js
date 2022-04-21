import {splitPathStr} from "../../utils/path";
import {globalNodesData} from "../../models/nodes";
import m from "mithril";
import routes from "../../utils/routes";


let NodeBreadcrumbs = {
  mapPathItems: function (pathItems) {
    let currentPath = "/";

    return pathItems.map((name) => {
      currentPath += name + "/";
      return {
        path: currentPath,
        name: name,
      }
    })
  },

  view: function () {
    const pathItems = this.mapPathItems(splitPathStr(globalNodesData.currentPath));

    return m("ol.breadcrumb mt-1 mb-1", [
      // Library list
      m("li.breadcrumb-item", m(m.route.Link, {
        href: routes.library_index,
        class: "btn btn-link btn-breadcrumb",
      }, "My libraries")),

      // Current library
      m("li.breadcrumb-item", m(m.route.Link, {
        class: ["btn", "btn-link", "btn-breadcrumb", pathItems.length === 0 ? "disabled" : null].join(" "),
        disabled: pathItems.length === 0,
        href: m.buildPathname(routes.library_nodes_path, {lib_id: globalNodesData.library.id, path: "/"})
      }, globalNodesData.library.name)),

      // Directories
      pathItems.map((pathItem, index, arr) => (
        m("li.breadcrumb-item", m(m.route.Link, {
          class: ["btn", "btn-link", "btn-breadcrumb", index === arr.length - 1 ? "disabled" : null].join(" "),
          href: m.buildPathname(routes.library_nodes_path, {lib_id: globalNodesData.library.id, path: pathItem.path})
        }, pathItem.name))
      )),
    ]);
  }
};


export default NodeBreadcrumbs;
