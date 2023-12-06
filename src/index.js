
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

// Initialize Firebase
const app = firebase.initializeApp(firebaseConfig);

var ui = new firebaseui.auth.AuthUI(firebase.auth());

var uiConfig = {
    callbacks: {
      signInSuccessWithAuthResult: function(authResult, redirectUrl) {
        // User successfully signed in.
        // Return type determines whether we continue the redirect automatically
        // or whether we leave that to developer to handle.
        return true;
      },
      uiShown: function() {
        // The widget is rendered.
        // Hide the loader.
        document.getElementById('loader').style.display = 'none';
      }
    },
    // Will use popup for IDP Providers sign-in flow instead of the default, redirect.
    signInFlow: 'popup',
    signInSuccessUrl: '/home',
    signInOptions: [
      // Leave the lines as is for the providers you want to offer your users.
      firebase.auth.GoogleAuthProvider.PROVIDER_ID,
    ],
  };

  ui.start('#firebaseui-auth-container', uiConfig);


