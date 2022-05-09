import m from 'mithril';
import {getCookie} from "../utils/cookie";


function CurrentUser(data) {
  this.fullName= data["full_name"] || "";
  this.isSuperuser= data["is_superuser"] || false;
}


const Auth = {
  currentUser: null,

  getCurrentUser: function() {
    return m.request({
      method: "GET",
      url: "/api/v1/sys/current_user",
    }).then((data) => {
      this.currentUser = new CurrentUser(data);
      return data;
    })
  },

  logout: function() {
    return m.request({
      method: "POST",
      url: '/api/v1/auth/logout',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      }
    })
  },
};


export default Auth;
