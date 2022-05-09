import {Loader} from "../../components/bootstrap/loader";
import m from "mithril";
import {FieldAttrs, FormAutoField, FormInput} from "../../components/bootstrap/form";
import {modal} from "../../components/bootstrap/modal";
import {getCookie} from "../../utils/cookie";


function DataSource(data) {
  this.id = data["id"] || null;
  this.name = data["name"] || "";
  this.data_provider_id = data["data_provider_id"] || null;
  this.options = data["options"] || {};
  this.actions = data["actions"] || {};

  Object.defineProperty(this, 'dataProviderId', {
    get: () => (this.data_provider_id),
    set: (value) => {this.data_provider_id = value}
  });

  this.toJSON = function() {
    return {
      id: this.id,
      name: this.name,
      data_provider_id: this.dataProviderId,
      options: this.options,
    }
  }
}


const dataSourceData = {
  list: [],

  getUrl: function(instance) {
    if (instance && instance.id) {
      return m.buildPathname("/api/v1/ds/:id", {id: instance.id})
    }
    return "/api/v1/ds";
  },
  fetch: function() {
    this.list.length = 0;
    return (
      m.request({
        method: "GET",
        url: this.getUrl(null),
      }).then((response) => {
        this.list = response.map((data) => (new DataSource(data)));
        return response;
      })
    );
  },
  save: function(instance) {
    return (
      m.request({
        method: instance.id ? "PUT" : "POST",
        url: this.getUrl(instance),
        body: instance.toJSON(),
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
        }
      })
    )
  },
  fetchOptions: function(instance, method) {
    return (
      m.request({
        method: "OPTIONS",
        url: this.getUrl(instance),
      }).then((data) => {
        return data["actions"][method].map((data) => (new FieldAttrs(data)));
      })
    )
  }
};


function showDataSourceMenu(dataSource) {
  let status = null;
  let instanceFields = [];
  const formData = new DataSource(Object.assign({}, dataSource));
  const dataProviderParams = {
    providerFields: {},
    fetch: function() {
      return (
        m.request({
          method: "GET",
          url: "/api/v1/dp",
        }).then((response) => {
          for (let provider of response) {
            this.providerFields[provider["id"]] = provider["fields"].map((attrs) => (new FieldAttrs(attrs)));
          }
          return response;
        })
      );
    }
  };

  Promise.all([
    dataProviderParams.fetch(),
    dataSourceData.fetchOptions(dataSource, dataSource ? "PUT" : "POST"),
  ]).then(([dpResponse, dsResponse]) => {
    status = "done";
    instanceFields = dsResponse;
  });


  function formSubmit(e) {
    e.preventDefault();
    dataSourceData.save(formData).then((response) => {
      if (dataSource) {
        Object.assign(dataSource, response);
      } else {
        dataSourceData.list.push(new DataSource(response))
      }
      modal.close();
    });
  }

  const EditNodeForm = {
    view: function() {
      if (status !== "done") return m(Loader);
      let optionFields = [];

      if (formData.dataProviderId) {
        optionFields = dataProviderParams.providerFields[formData.dataProviderId];
      }

      return (
        m("form", {onsubmit: formSubmit}, [

          instanceFields.map((fieldAttrs) => (
            m(FormAutoField, {
              instance: formData,
              fieldAttrs: fieldAttrs,
            })
          )),

          m("legend.h5", "Options"),

          optionFields.map((fieldAttrs) => (
            m(FormAutoField, {
              instance: formData.options,
              fieldAttrs: fieldAttrs,
              trueValue: "true",
              falseValue: "false",
            })
          ))
        ])
      )
    }
  };

  const buttonOk = {
    view: () => (m("button.btn btn-primary[type=button]", {onclick: formSubmit}, "Submit"))
  };

  modal.show({
    buttons: [modal.BtnCancel, buttonOk],
    title: "Node settings",
  }, EditNodeForm)
}


const ProviderItemView = {
  view: function(vnode) {
    const {item} = vnode.attrs;

    return [
      m("table.table table-hover mb-0", [
        m("tbody",
          m("tr", [
            m("td", "id"),
            m("td", item.id),
          ]),
          m("tr", [
            m("td", "Data provider"),
            m("td", item.dataProviderId),
          ]),
        ),
      ]),
      m("div.card-footer", [
        m("button.btn btn-secondary[role=button]", {onclick: () => {showDataSourceMenu(item)}}, "Edit")
      ])
    ]
  },
};


const DataProviderAccordion = {
  //todo: add collapsing animation
  oninit: function() {
    this.selectedItem = null;
  },

  selectItem: function(item) {
    if (this.selectedItem === item) {
      this.selectedItem = null;
    } else {
      this.selectedItem = item;
    }
  },

  view: function(vnode) {
    const {items=[]} = vnode.attrs;

    return (
      m("div.accordion", items.map((item) => {
        const isSelected = this.selectedItem === item;

        return (
          m("div.accordion-item", [
            m("h2.accordion-header",
              m("button.accordion-button[type=button]", {
                onclick: this.selectItem.bind(this, item),
                class: isSelected ? null : "collapsed",
              }, m("span", [m("i.fa-solid fa-database me-1"), item.name]))
            ),
            m("div.accordion-collapse collapse border border-primary border-top-0",
              {class: isSelected ? "show" : null},
              m(ProviderItemView, {item: item}),
            )
          ])
        )
      }))
    )
  }
};


const DataSourceTopNavBar = {
  view: function() {
    return (
      m("button.btn btn-secondary btn-sm me-1 ms-1[role=button]", {onclick: () => {showDataSourceMenu(null)}}, [
        m("i.fa-solid fa-plus"),
        m("span.d-none d-sm-inline ps-1", "Create Data source"),
      ])
    )
  }
};


const DataSourceSettingsView = {
  verboseName: "Data source",
  iconClass: "fa-solid fa-database",
  TopNavView: DataSourceTopNavBar,

  oninit: function() {
    this.status = "loading";
    return dataSourceData.fetch().then((data) => {
      this.status = "done";
      return data;
    });
  },

  view: function() {
    if (this.status !== 'done') return m(Loader);
    if (dataSourceData.list.length === 0) return m("div.alert.alert-secondary", "No data sources");

    return [
      m(DataProviderAccordion, {items: dataSourceData.list}),
    ];
  }
};


export default DataSourceSettingsView;
