import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import TransactionsPage from "./pages/TransactionsPage";
import DashboardPage from "./pages/DashboardPage";
import DailySpendingPage from "./pages/DailySpendingPage";
import BigPurchasesPage from "./pages/BigPurchasesPage";
import TravelPage from "./pages/TravelPage";
import Layout from "./components/Layout";
import PrivateRoute from "./components/PrivateRoute";
import { AuthProvider } from "./contexts/AuthContext";
import { ToastProvider } from "./components/ui/use-toast";

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Router>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<LoginPage />} />
              <Route path="signup" element={<SignupPage />} />
              <Route
                path="dashboard"
                element={
                  <PrivateRoute>
                    <DashboardPage />
                  </PrivateRoute>
                }
              />
              <Route
                path="transactions"
                element={
                  <PrivateRoute>
                    <TransactionsPage />
                  </PrivateRoute>
                }
              />
              <Route
                path="daily-spending"
                element={
                  <PrivateRoute>
                    <DailySpendingPage />
                  </PrivateRoute>
                }
              />
              <Route
                path="big-purchases"
                element={
                  <PrivateRoute>
                    <BigPurchasesPage />
                  </PrivateRoute>
                }
              />
              <Route
                path="travel"
                element={
                  <PrivateRoute>
                    <TravelPage />
                  </PrivateRoute>
                }
              />
            </Route>
          </Routes>
        </Router>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
