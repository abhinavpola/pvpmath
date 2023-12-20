
import firebase from "firebase/compat/app";
import "firebase/compat/auth";
var firebaseui = require('firebaseui');

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCdkTW8_96C9rUYlNJ8UZC0O4r1164_wUo",
  authDomain: "pvpmath.firebaseapp.com",
  projectId: "pvpmath",
  storageBucket: "pvpmath.appspot.com",
  messagingSenderId: "429238157655",
  appId: "1:429238157655:web:116e8b4891ed8549a6be12",
  measurementId: "G-1EKPNGQW9J"
};

function appleProvider() {
  const provider = new firebase.auth.OAuthProvider('apple.com');
  provider.addScope('email');
  provider.addScope('name');
  return provider.providerId;
}

// Initialize Firebase
const app = firebase.initializeApp(firebaseConfig);

var ui = new firebaseui.auth.AuthUI(firebase.auth());

var uiConfig = {
  callbacks: {
    signInSuccessWithAuthResult: function (authResult, redirectUrl) {
      // User successfully signed in.
      var user = authResult.user;

      // Do something with the returned AuthResult.
      // Return type determines whether we continue the redirect automatically
      // or whether we leave that to developer to handle.

      user.getIdToken().then(function (idToken) {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/login", true);
        xhr.setRequestHeader('Content-type', 'application/json;charset=UTF-8');
        xhr.onreadystatechange = function () {
          if (this.readyState == 4 && this.status == 200) {
            return true;
          }
          else {
            console.log(xhr.statusText);
            return false;
          }
        };
        var data = JSON.stringify({ "idToken": String(idToken) });
        xhr.send(data);

        setTimeout(function () {
          window.location.assign("/home");
      }, 1000);
      });

      // Return type determines whether we continue the redirect automatically
      // or whether we leave that to the developer to handle.
      return false;
    },
    uiShown: function () {
      // The widget is rendered.
      // Hide the loader.
      document.getElementById('loader').style.display = 'none';
    }
  },
  // Will use popup for IDP Providers sign-in flow instead of the default, redirect.
  signInFlow: 'popup',
  signInOptions: [
    // Leave the lines as is for the providers you want to offer your users.
    firebase.auth.GoogleAuthProvider.PROVIDER_ID,
    firebase.auth.GithubAuthProvider.PROVIDER_ID,
    appleProvider(),
  ],
};

ui.start('#firebaseui-auth-container', uiConfig);
