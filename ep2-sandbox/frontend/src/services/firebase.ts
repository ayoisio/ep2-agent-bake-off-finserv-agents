// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyALJsfSVK-N2EwVtx5j-pmDGPL4xNtMgNk",
  authDomain: "agent-bake-off-episode-2.firebaseapp.com",
  projectId: "agent-bake-off-episode-2",
  storageBucket: "agent-bake-off-episode-2.firebasestorage.app",
  messagingSenderId: "609099553774",
  appId: "1:609099553774:web:28b323af3a21e022470cff",
  measurementId: "G-2TZG9TXSVH",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Analytics (optional - only works in browser)
let analytics;
if (typeof window !== "undefined") {
  analytics = getAnalytics(app);
}

// Initialize Auth
export const auth = getAuth(app);

// Initialize Firestore
export const db = getFirestore(app);

export { analytics };
export default app;
