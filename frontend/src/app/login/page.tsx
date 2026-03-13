"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { DollarSign, Eye, EyeOff, Loader2 } from "lucide-react";
import api from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await api.post<{ access_token: string; token_type: string }>(
        "/auth/login",
        { email, password }
      );

      localStorage.setItem("auth_token", data.access_token);

      // Fetch user info
      const user = await api.get<{ name: string; role: string; id: string }>(
        "/auth/me"
      );
      localStorage.setItem("user_name", user.name);
      localStorage.setItem("user_role", user.role);
      localStorage.setItem("user_id", user.id);

      router.push("/dashboard");
    } catch {
      setError("Email ou senha incorretos. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE4YzAtNC45NzEtNC4wMjktOS05LTlzLTkgNC4wMjktOSA5IDQuMDI5IDkgOSA5IDktNC4wMjkgOS05eiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
        <div className="relative z-10 text-center px-8 max-w-lg">
          <div className="w-20 h-20 rounded-2xl bg-white/20 flex items-center justify-center mx-auto mb-8">
            <DollarSign className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">BudgetPro</h1>
          <p className="text-lg text-white/80 mb-8">
            Plataforma de Controle Orçamentário Corporativo
          </p>
          <div className="grid grid-cols-2 gap-4 text-left">
            {[
              "Planejamento Orçamentário",
              "Dashboards Executivos",
              "Forecast Inteligente",
              "Controle de Versões",
            ].map((feature) => (
              <div
                key={feature}
                className="flex items-center gap-2 text-white/90 text-sm"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-white/60" />
                {feature}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel - Login form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-8 justify-center">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-primary-foreground" />
            </div>
            <span className="font-bold text-2xl">BudgetPro</span>
          </div>

          <h2 className="text-2xl font-bold text-foreground mb-2">
            Bem-vindo de volta
          </h2>
          <p className="text-muted-foreground mb-8">
            Entre com suas credenciais para acessar a plataforma
          </p>

          <form onSubmit={handleLogin} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                className="w-full px-4 py-2.5 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Senha
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Sua senha"
                  className="w-full px-4 py-2.5 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                "Entrar"
              )}
            </button>
          </form>

          <div className="mt-6 p-4 rounded-lg bg-muted/50 border border-border">
            <p className="text-xs text-muted-foreground font-medium mb-2">
              Contas de demonstração:
            </p>
            <div className="space-y-1 text-xs text-muted-foreground">
              <p>
                <span className="font-medium">Admin:</span>{" "}
                admin@budgetpro.com / admin123
              </p>
              <p>
                <span className="font-medium">Financeiro:</span>{" "}
                financeiro@budgetpro.com / fin123
              </p>
              <p>
                <span className="font-medium">Gestor:</span>{" "}
                gestor@budgetpro.com / gest123
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
