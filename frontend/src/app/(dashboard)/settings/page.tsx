"use client";

import { useState } from "react";
import { Settings, Building2, Database, Bell, Shield, Globe, Save } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("company");

  const tabs = [
    { id: "company", label: "Empresa", icon: Building2 },
    { id: "integrations", label: "Integrações", icon: Database },
    { id: "notifications", label: "Notificações", icon: Bell },
    { id: "security", label: "Segurança", icon: Shield },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Configurações</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Configurações gerais da plataforma
        </p>
      </div>

      <div className="flex gap-6">
        {/* Tabs sidebar */}
        <div className="w-56 flex-shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left",
                  activeTab === tab.id
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent"
                )}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 rounded-xl border border-border bg-card p-6 shadow-sm">
          {activeTab === "company" && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-foreground">
                Dados da Empresa
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Nome da Empresa
                  </label>
                  <input
                    type="text"
                    defaultValue="TechCorp S.A."
                    className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    CNPJ
                  </label>
                  <input
                    type="text"
                    defaultValue="12.345.678/0001-90"
                    className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Ano Fiscal Atual
                  </label>
                  <input
                    type="number"
                    defaultValue="2026"
                    className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Moeda
                  </label>
                  <select className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                    <option>BRL - Real Brasileiro</option>
                    <option>USD - Dólar Americano</option>
                    <option>EUR - Euro</option>
                  </select>
                </div>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors">
                <Save className="w-4 h-4" />
                Salvar Alterações
              </button>
            </div>
          )}

          {activeTab === "integrations" && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-foreground">
                Integrações com ERP
              </h3>
              <div className="space-y-4">
                {[
                  { name: "SAP", status: "disconnected", description: "SAP S/4HANA ou SAP Business One" },
                  { name: "Oracle", status: "disconnected", description: "Oracle ERP Cloud ou NetSuite" },
                  { name: "Totvs", status: "connected", description: "Totvs Protheus ou RM" },
                  { name: "Planilhas Excel", status: "connected", description: "Importação/Exportação via Excel" },
                ].map((integration) => (
                  <div
                    key={integration.name}
                    className="flex items-center justify-between p-4 rounded-lg border border-border"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
                        <Database className="w-5 h-5 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="font-medium text-sm text-foreground">
                          {integration.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {integration.description}
                        </p>
                      </div>
                    </div>
                    <button
                      className={cn(
                        "text-xs px-3 py-1.5 rounded-lg font-medium transition-colors",
                        integration.status === "connected"
                          ? "bg-green-100 text-green-800"
                          : "border border-border hover:bg-accent"
                      )}
                    >
                      {integration.status === "connected"
                        ? "Conectado"
                        : "Conectar"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "notifications" && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-foreground">
                Preferências de Notificação
              </h3>
              <div className="space-y-4">
                {[
                  { label: "Alerta de desvio orçamentário (>10%)", enabled: true },
                  { label: "Nova versão de orçamento criada", enabled: true },
                  { label: "Orçamento aprovado", enabled: true },
                  { label: "Comentário em linha de orçamento", enabled: false },
                  { label: "Importação de dados concluída", enabled: true },
                  { label: "Relatório semanal por email", enabled: false },
                ].map((notif, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between py-3 border-b border-border last:border-0"
                  >
                    <span className="text-sm text-foreground">
                      {notif.label}
                    </span>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        defaultChecked={notif.enabled}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all" />
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-foreground">
                Segurança
              </h3>
              <div className="space-y-4">
                <div className="p-4 rounded-lg border border-border">
                  <h4 className="text-sm font-medium text-foreground mb-2">
                    Política de Senhas
                  </h4>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p>• Mínimo de 8 caracteres</p>
                    <p>• Deve conter letras e números</p>
                    <p>• Expiração a cada 90 dias</p>
                  </div>
                </div>
                <div className="p-4 rounded-lg border border-border">
                  <h4 className="text-sm font-medium text-foreground mb-2">
                    Sessão
                  </h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-foreground">
                        Tempo de expiração da sessão
                      </span>
                      <select className="px-3 py-1.5 rounded-lg border border-input bg-background text-sm">
                        <option>8 horas</option>
                        <option>12 horas</option>
                        <option>24 horas</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
