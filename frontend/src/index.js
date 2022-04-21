import m from "mithril";
import {globalNodesData, Node} from "./models/nodes";
import {NodeListWrapperView} from "./views/node_list/index";
import routes from "./utils/routes";
import {parsePath} from "./utils/path";
import LibraryListWrapperView from "./views/library_list/index";


let NodeListRouter = {
  onmatch: (args, requestedPath) => {
    let path = parsePath(decodeURI(requestedPath)) || "/";
    globalNodesData.fetch(args.lib_id, path);
  },
  render: () => (m(NodeListWrapperView)),
};


m.route(document.body, routes.library_index, {
  [routes.library_index]: LibraryListWrapperView,
  [routes.library_nodes_path]: NodeListRouter,
});


//debug
window.m = m;
window.g = globalNodesData;
window.g.Node = Node;