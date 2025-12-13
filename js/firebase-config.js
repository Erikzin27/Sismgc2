// Importa as funções necessárias do Firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// ⚠️ SUBSTITUA PELOS SEUS DADOS DO FIREBASE CONSOLE
const firebaseConfig = {
  apiKey: "AIzaSyB3dLUPQA5M5DGbsLGOda9CJTFqvM9OhQg",
  authDomain: "granjaweb-9b4cc.firebaseapp.com",
  projectId: "granjaweb-9b4cc",
  storageBucket: "granjaweb-9b4cc.firebasestorage.app",
  messagingSenderId: "285050858452",
  appId: "1:285050858452:web:afe549166d6e22a9418441",
  measurementId: "G-R2YTE8M5K3"
};

// Inicializa o Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// Exporta o banco de dados para usar no app.js
export { db };