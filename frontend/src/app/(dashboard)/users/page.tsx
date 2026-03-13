"use client";

import { useState } from "react";
import { Users, Plus, Search, Shield, Eye, Edit, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface UserItem {
  id: string;
  name: string;
  email: string;
  role: string;
  isActive: boolean;
  createdAt: string;
}

const MOCK_USERS: UserItem[] = [
  { id: "1", name: "Administrador", email: "admin@budgetpro.com", role: "admin", isActive: true, createdAt: "2025-11-01" },
  { id: "2", name: "Ana Financeiro", email: "financeiro@budgetpro.com", role: "financial", isActive: true, createdAt: "2025-11-15" },
  { id: "3", name: "Pedro Gestor", email: "gestor@budgetpro.com", role: "manager", isActive: true, createdAt: "2025-12-01" },
  { id: "4", name: "Maria Viewer", email: "viewer@budgetpro.com", role: "viewer", isActive: true, createdAt: "2026-01-10" },
  { id: "5", name: "Carlos Mendes", email: "carlos@techcorp.com", role: "manager", isActive: true, createdAt: "2026-01-15" },
  { id: "6", name: "Fernanda Lima", email: "fernanda@techcorp.com", role: "viewer", isActive: false, createdAt: "2026-02-01" },
];

const roleConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  admin: { label: "Administrador", color: "bg-red-100 text-red-800", icon: Shield },
  financial: { label: "Financeiro", color: "bg-blue-100 text-blue-800", icon: Edit },
  manager: { label: "Gestor de Área", color: "bg-purple-100 text-purple-800", icon: Users },
  viewer: { label: "Visualização", color: "bg-gray-100 text-gray-800", icon: Eye },
};

const permissionMatrix = [
  { permission: "Editar orçamento", admin: true, financial: true, manager: true, viewer: false },
  { permission: "Aprovar orçamento", admin: true, financial: true, manager: false, viewer: false },
  { permission: "Visualizar dashboards", admin: true, financial: true, manager: true, viewer: true },
  { permission: "Importar dados", admin: true, financial: true, manager: false, viewer: false },
  { permission: "Gerenciar usuários", admin: true, financial: false, manager: false, viewer: false },
  { permission: "Exportar relatórios", admin: true, financial: true, manager: true, viewer: true },
  { permission: "Gerar forecast", admin: true, financial: true, manager: true, viewer: false },
  { permission: "Bloquear versões", admin: true, financial: true, manager: false, viewer: false },
];

export default function UsersPage() {
  const [search, setSearch] = useState("");
  const [showPermissions, setShowPermissions] = useState(false);

  const filtered = MOCK_USERS.filter(
    (u) =>
      !search ||
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Usuários</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Gerencie usuários e permissões da plataforma
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPermissions(!showPermissions)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors",
              showPermissions
                ? "border-primary bg-primary/10 text-primary"
                : "border-border hover:bg-accent"
            )}
          >
            <Shield className="w-4 h-4" />
            Matriz de Permissões
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors">
            <Plus className="w-4 h-4" />
            Novo Usuário
          </button>
        </div>
      </div>

      {/* Permission Matrix */}
      {showPermissions && (
        <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
          <div className="p-4 border-b border-border bg-muted/30">
            <h3 className="text-sm font-semibold text-foreground">
              Matriz de Permissões por Perfil
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/50 border-b border-border">
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground text-xs uppercase">
                    Permissão
                  </th>
                  {Object.entries(roleConfig).map(([key, config]) => (
                    <th
                      key={key}
                      className="text-center py-3 px-4 font-medium text-muted-foreground text-xs uppercase"
                    >
                      {config.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {permissionMatrix.map((row, idx) => (
                  <tr
                    key={row.permission}
                    className={cn(
                      "border-b border-border",
                      idx % 2 === 0 ? "bg-card" : "bg-muted/20"
                    )}
                  >
                    <td className="py-2.5 px-4 text-foreground font-medium">
                      {row.permission}
                    </td>
                    {(["admin", "financial", "manager", "viewer"] as const).map(
                      (role) => (
                        <td key={role} className="py-2.5 px-4 text-center">
                          {row[role] ? (
                            <span className="inline-flex w-5 h-5 rounded-full bg-green-100 items-center justify-center">
                              <span className="text-green-600 text-xs">✓</span>
                            </span>
                          ) : (
                            <span className="inline-flex w-5 h-5 rounded-full bg-red-50 items-center justify-center">
                              <span className="text-red-400 text-xs">✕</span>
                            </span>
                          )}
                        </td>
                      )
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Buscar por nome ou email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Users List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((user) => {
          const config = roleConfig[user.role];
          const RoleIcon = config.icon;

          return (
            <div
              key={user.id}
              className="rounded-xl border border-border bg-card p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-sm text-foreground truncate">
                      {user.name}
                    </h3>
                    {!user.isActive && (
                      <span className="text-xs bg-red-100 text-red-800 px-1.5 py-0.5 rounded">
                        Inativo
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {user.email}
                  </p>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <span
                  className={cn(
                    "flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium",
                    config.color
                  )}
                >
                  <RoleIcon className="w-3 h-3" />
                  {config.label}
                </span>
                <span className="text-xs text-muted-foreground">
                  Desde{" "}
                  {new Date(user.createdAt).toLocaleDateString("pt-BR")}
                </span>
              </div>

              <div className="mt-3 pt-3 border-t border-border flex gap-2">
                <button className="flex-1 text-xs py-1.5 rounded-md border border-border hover:bg-accent transition-colors font-medium">
                  Editar
                </button>
                <button className="flex-1 text-xs py-1.5 rounded-md border border-border hover:bg-accent transition-colors font-medium text-destructive">
                  {user.isActive ? "Desativar" : "Ativar"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
