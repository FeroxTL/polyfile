import m from "mithril";


function Library(data) {
  this.name = data["name"] || "";
  this.id = data["id"] || null;
  // Object.assign(this, data);
}


let LibraryData = function () {
  this.list = [];
  this.status = null;
  this.error = null;

  this.fetch = function () {
    this.status = "loading";
    m.request({
      method: "GET",
      url: "/api/v1/libraries",
    }).then((result) => {
      this.status = "done";
      this.list = result.map((data) => (new Library(data)));
    }).catch((e) => {
      this.error = e.message;
    });
  };

  this.addLibrary = (library) => {
    this.list.push(library);
  };

  this.removeLibrary = (library) => {
    const index = this.list.indexOf(library);
    if (index > -1) {
      this.list.splice(index, 1);
    }
  }
};


let globalLibraryData = new LibraryData();


export {globalLibraryData, Library};
