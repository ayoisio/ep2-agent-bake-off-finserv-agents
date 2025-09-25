import React, { useEffect, useState } from "react";
import { Outlet, useSearchParams, useNavigate } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";
import { fetchUser } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";

interface User {
  name: string;
  profile_picture: string;
}

const Layout: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [searchParams] = useSearchParams();
  const userId = searchParams.get("userId");
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const loadUser = async () => {
      try {
        // Use a default userId if none provided (for demo purposes)
        const userIdToUse = userId || "user-002";
        const userData = await fetchUser(userIdToUse);
        setUser(userData);
      } catch (err) {
        console.error("Failed to load user data");
      }
    };

    loadUser();
  }, [userId]);

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/");
    } catch (error) {
      console.error("Failed to logout:", error);
    }
  };

  return (
    <div
      className="relative flex size-full min-h-screen flex-col bg-background group/design-root overflow-x-hidden "
      style={{ fontFamily: '"Public Sans", "Noto Sans", sans-serif' }}
    >
      <Navbar
        userName={currentUser?.displayName || user?.name}
        profilePicture={currentUser?.photoURL || user?.profile_picture}
        currentUser={currentUser}
        onLogout={handleLogout}
      />
      <main className="flex-1 pb-20">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
