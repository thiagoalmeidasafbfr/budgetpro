"use client";

import { Bell, LogOut, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export function Header() {
  const router = useRouter();
  const [userName, setUserName] = useState("Usuário");
  const [userRole, setUserRole] = useState("");

  useEffect(() => {
    const name = localStorage.getItem("user_name");
    const role = localStorage.getItem("user_role");
    if (name) setUserName(name);
    if (role) setUserRole(role);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_name");
    localStorage.removeItem("user_role");
    router.push("/login");
  };

  const roleLabels: Record<string, string> = {
    admin: "Administrador",
    financial: "Financeiro",
    manager: "Gestor",
    viewer: "Visualizador",
  };

  return (
    <header className="h-16 border-b border-border bg-card px-6 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h2 className="text-sm text-muted-foreground">Bem-vindo,</h2>
        <p className="text-sm font-semibold text-foreground">{userName}</p>
      </div>
      <div className="flex items-center gap-4">
        {userRole && (
          <span className="text-xs bg-primary/10 text-primary px-2.5 py-1 rounded-full font-medium">
            {roleLabels[userRole] || userRole}
          </span>
        )}
        <button className="relative p-2 rounded-lg hover:bg-accent text-muted-foreground transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full" />
        </button>
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <User className="w-4 h-4 text-primary" />
        </div>
        <button
          onClick={handleLogout}
          className="p-2 rounded-lg hover:bg-accent text-muted-foreground transition-colors"
          title="Sair"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
