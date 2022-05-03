import m from "mithril";


function Node(data) {
  this.name = data["name"] || "";
  this.path = data["path"] || "/";
  this.fileType = data["file_type"] || "unknown";
  this.library = data["library"] || null;
  this.size = data["size"] || null;
  this.mimeType = data["mimetype"] || null;

  Object.defineProperty(this, 'isFile', {
    get: () => (this["fileType"] === "file")
  });
  Object.defineProperty(this, 'isDirectory', {
    get: () => (this["fileType"] === "directory")
  });
  Object.defineProperty(this, 'fullPath', {
    get: () => (this.path + this.name + (this.fileType === "directory" ? "/" : ""))
  });
  Object.defineProperty(this, 'downloadUrl', {
    get: () => ("/api/v1/lib/" + this.library.id + "/download" + this.fullPath)
  });
}


let NodesData = function () {
  this.list = [];
  this.status = null;
  this.error = null;
  this.library = null;
  this.currentPath = null;

  this.fetch = (lib_id, path) => {
    this.status = "loading";
    this.list = [];
    this.currentPath = path;

    m.request({
      method: "GET",
      url: "/api/v1/lib/:lib_id/files:path",
      params: {lib_id: lib_id, path: path},
    }).then((result) => {
      this.status = "done";
      this.library = result["library"];
      this.list = result.nodes.map((data) => (
        new Node({library: result.library, path: path, ...data}))
      );
    }).catch((e) => {
      this.error = e.message;
    });
  };

  this.resort = () => {
    let compareNodes = (a, b) => {
      if (a.fileType !== b.fileType) {
        return a.isFile ? 1 : -1;
      }
      return a.name > b.name ? 1 : -1;
    };

    this.list.sort(compareNodes);
  };

  this.addNode = (node) => {
    this.list.push(node);
    this.resort();
  };

  this.removeNode = (node) => {
    const index = this.list.indexOf(node);
    if (index > -1) {
      this.list.splice(index, 1);
    }
  }
};


let globalNodesData = new NodesData();


export {globalNodesData, Node};
