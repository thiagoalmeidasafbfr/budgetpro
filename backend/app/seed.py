"""
Seed script for BudgetPro.

Usage:
    python -m app.seed
"""

import random
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
from app.models.models import (
    Company, User, Department, CostCenter, Account, BudgetVersion,
    Budget, Actual, Forecast, Comment, AuditLog,
    UserRole, AccountCategory, VersionStatus, ActualSource, ForecastMethod, AuditAction,
)
from app.auth.auth import hash_password

# Fixed seed for reproducibility
random.seed(42)

MONTH_COLS = ["jan", "feb", "mar", "apr", "may", "jun",
              "jul", "aug", "sep", "oct", "nov", "dec"]


def vary(base: float, pct: float = 0.10) -> Decimal:
    """Apply random variation of +/- pct around a base value."""
    factor = 1.0 + random.uniform(-pct, pct)
    return Decimal(str(round(base * factor, 2)))


def seasonal_revenue(base: float, month: int) -> Decimal:
    """Revenue with seasonal pattern: higher in Q2 (Apr-Jun) and Q4 (Oct-Dec)."""
    seasonal = {
        1: 0.85, 2: 0.88, 3: 0.92,
        4: 1.10, 5: 1.15, 6: 1.20,
        7: 0.90, 8: 0.88, 9: 0.95,
        10: 1.10, 11: 1.18, 12: 1.25,
    }
    return vary(base * seasonal[month])


def marketing_seasonal(base: float, month: int) -> Decimal:
    """Marketing: higher in Jan and Jun."""
    seasonal = {
        1: 1.40, 2: 0.90, 3: 0.85,
        4: 0.95, 5: 1.00, 6: 1.35,
        7: 0.90, 8: 0.85, 9: 0.95,
        10: 1.05, 11: 1.10, 12: 1.00,
    }
    return vary(base * seasonal[month])


def salary_monthly(base: float, month: int) -> Decimal:
    """Salaries: consistent with slight increases mid-year."""
    seasonal = {
        1: 1.00, 2: 1.00, 3: 1.00,
        4: 1.00, 5: 1.02, 6: 1.02,
        7: 1.03, 8: 1.03, 9: 1.03,
        10: 1.05, 11: 1.05, 12: 1.05,
    }
    return vary(base * seasonal[month], 0.03)


def flat_monthly(base: float, month: int) -> Decimal:
    """Relatively flat monthly values with slight random variation."""
    return vary(base)


# Base monthly values by account code
ACCOUNT_BASE_VALUES = {
    # Revenue (monthly base per cost center)
    "3.1.01": 150000.0,
    "3.1.02": 80000.0,
    "3.1.03": 45000.0,
    # Cost
    "4.1.01": 90000.0,
    "4.1.02": 35000.0,
    # Expense
    "5.1.01": 85000.0,
    "5.1.02": 18000.0,
    "5.1.03": 22000.0,
    "5.1.04": 8000.0,
    "5.1.05": 3000.0,
    "5.1.06": 12000.0,
    "5.1.07": 25000.0,
    "5.1.08": 15000.0,
    "5.1.09": 6000.0,
    "5.1.10": 4500.0,
    # Investment
    "6.1.01": 10000.0,
    "6.1.02": 8000.0,
    "6.1.03": 3000.0,
    "6.1.04": 5000.0,
    "6.1.05": 7000.0,
}

# Which monthly pattern function to use per account code
ACCOUNT_PATTERN = {
    "3.1.01": seasonal_revenue,
    "3.1.02": seasonal_revenue,
    "3.1.03": seasonal_revenue,
    "4.1.01": flat_monthly,
    "4.1.02": flat_monthly,
    "5.1.01": salary_monthly,
    "5.1.02": flat_monthly,
    "5.1.03": flat_monthly,
    "5.1.04": flat_monthly,
    "5.1.05": flat_monthly,
    "5.1.06": flat_monthly,
    "5.1.07": marketing_seasonal,
    "5.1.08": flat_monthly,
    "5.1.09": flat_monthly,
    "5.1.10": flat_monthly,
    "6.1.01": flat_monthly,
    "6.1.02": flat_monthly,
    "6.1.03": flat_monthly,
    "6.1.04": flat_monthly,
    "6.1.05": flat_monthly,
}

# Scaling factor per cost center to differentiate sizes
CC_SCALE = {
    "CC001": 0.60,
    "CC002": 0.45,
    "CC003": 1.20,
    "CC004": 0.80,
    "CC005": 1.00,
    "CC006": 0.70,
    "CC007": 0.35,
    "CC008": 0.40,
}

VENDORS = [
    "Fornecedor Alpha Ltda",
    "Fornecedor Beta S.A.",
    "Google Cloud Platform",
    "Amazon Web Services",
    "Microsoft Azure",
    "Algar Telecom",
    "Vivo Empresas",
    "Sodexo Beneficios",
    "Ticket Restaurante",
    "Localiza Rent a Car",
    "Booking.com Business",
    "Graffit Papelaria",
    "TechParts Informatica",
    "Siemens Energia",
    "Porto Seguro Seguros",
    "Bradesco Seguros",
    "WeWork Coworking",
    "Stefanini Consultoria",
    "Deloitte Consultoria",
    "KPMG Auditoria",
    "Catho Online",
    "LinkedIn Recruiter",
    "Meta Ads",
    "Google Ads",
]


def run_seed():
    print("=" * 60)
    print("BudgetPro - Database Seed Script")
    print("=" * 60)

    # Create all tables
    print("\n[1/10] Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # Check if data already exists
        existing_company = db.query(Company).first()
        if existing_company:
            print("\nData already exists in the database. Skipping seed.")
            print("To re-seed, drop all tables first.")
            return

        # ---- Company ----
        print("[2/10] Creating company...")
        company = Company(
            name="TechCorp S.A.",
            cnpj="12.345.678/0001-90",
        )
        db.add(company)
        db.flush()
        print(f"  -> Company: {company.name} (ID: {company.id})")

        # ---- Users ----
        print("[3/10] Creating users...")
        users_data = [
            ("Admin BudgetPro", "admin@budgetpro.com", "admin123", UserRole.admin),
            ("Maria Financeiro", "financeiro@budgetpro.com", "fin123", UserRole.financial),
            ("Joao Gestor", "gestor@budgetpro.com", "gest123", UserRole.manager),
            ("Ana Viewer", "viewer@budgetpro.com", "view123", UserRole.viewer),
        ]
        users = {}
        for name, email, password, role in users_data:
            user = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=role,
                company_id=company.id,
            )
            db.add(user)
            db.flush()
            users[email] = user
            print(f"  -> User: {email} ({role.value})")

        admin_user = users["admin@budgetpro.com"]

        # ---- Departments ----
        print("[4/10] Creating departments...")
        dept_names = ["Financeiro", "Comercial", "Tecnologia", "Recursos Humanos"]
        departments = {}
        for dept_name in dept_names:
            dept = Department(
                name=dept_name,
                company_id=company.id,
            )
            db.add(dept)
            db.flush()
            departments[dept_name] = dept
            print(f"  -> Department: {dept_name}")

        # ---- Cost Centers ----
        print("[5/10] Creating cost centers...")
        cc_data = [
            ("CC001", "Tesouraria", "Financeiro"),
            ("CC002", "Contabilidade", "Financeiro"),
            ("CC003", "Vendas Nacionais", "Comercial"),
            ("CC004", "Vendas Internacionais", "Comercial"),
            ("CC005", "Desenvolvimento", "Tecnologia"),
            ("CC006", "Infraestrutura TI", "Tecnologia"),
            ("CC007", "Recrutamento", "Recursos Humanos"),
            ("CC008", "Treinamento", "Recursos Humanos"),
        ]
        cost_centers = {}
        for code, name, dept_name in cc_data:
            cc = CostCenter(
                code=code,
                name=name,
                department_id=departments[dept_name].id,
            )
            db.add(cc)
            db.flush()
            cost_centers[code] = cc
            print(f"  -> Cost Center: {code} - {name} ({dept_name})")

        # ---- Accounts ----
        print("[6/10] Creating accounts...")
        accounts_data = [
            # Revenue
            ("3.1.01", "Receita de Vendas Nacionais", AccountCategory.revenue),
            ("3.1.02", "Receita de Vendas Internacionais", AccountCategory.revenue),
            ("3.1.03", "Receita de Servicos", AccountCategory.revenue),
            # Cost
            ("4.1.01", "Custo de Mercadoria Vendida", AccountCategory.cost),
            ("4.1.02", "Custo de Servicos Prestados", AccountCategory.cost),
            # Expense
            ("5.1.01", "Salarios e Encargos", AccountCategory.expense),
            ("5.1.02", "Beneficios", AccountCategory.expense),
            ("5.1.03", "Aluguel e Condominio", AccountCategory.expense),
            ("5.1.04", "Energia e Telecomunicacoes", AccountCategory.expense),
            ("5.1.05", "Material de Escritorio", AccountCategory.expense),
            ("5.1.06", "Viagens e Hospedagem", AccountCategory.expense),
            ("5.1.07", "Marketing e Publicidade", AccountCategory.expense),
            ("5.1.08", "Consultoria e Assessoria", AccountCategory.expense),
            ("5.1.09", "Manutencao e Reparos", AccountCategory.expense),
            ("5.1.10", "Seguros", AccountCategory.expense),
            # Investment
            ("6.1.01", "Licencas de Software", AccountCategory.investment),
            ("6.1.02", "Equipamentos de TI", AccountCategory.investment),
            ("6.1.03", "Moveis e Utensilios", AccountCategory.investment),
            ("6.1.04", "Veiculos", AccountCategory.investment),
            ("6.1.05", "Obras e Reformas", AccountCategory.investment),
        ]
        accounts = {}
        for code, name, category in accounts_data:
            acc = Account(
                code=code,
                name=name,
                category=category,
            )
            db.add(acc)
            db.flush()
            accounts[code] = acc
            print(f"  -> Account: {code} - {name} ({category.value})")

        # ---- Budget Versions ----
        print("[7/10] Creating budget versions...")
        version_original = BudgetVersion(
            name="Budget 2026 Original",
            year=2026,
            status=VersionStatus.approved,
            company_id=company.id,
            created_by=admin_user.id,
            description="Orcamento original aprovado para o ano fiscal de 2026.",
        )
        db.add(version_original)
        db.flush()
        print(f"  -> Version: {version_original.name} (approved)")

        version_forecast = BudgetVersion(
            name="Forecast Q1 2026",
            year=2026,
            status=VersionStatus.draft,
            company_id=company.id,
            created_by=admin_user.id,
            description="Forecast revisado apos o primeiro trimestre de 2026.",
        )
        db.add(version_forecast)
        db.flush()
        print(f"  -> Version: {version_forecast.name} (draft)")

        # ---- Budget Rows ----
        print("[8/10] Creating budget entries (cost_center x account)...")
        budget_entries = {}
        budget_count = 0
        for cc_code, cc in cost_centers.items():
            scale = CC_SCALE.get(cc_code, 1.0)
            for acc_code, acc in accounts.items():
                base = ACCOUNT_BASE_VALUES[acc_code] * scale
                pattern_fn = ACCOUNT_PATTERN[acc_code]

                month_values = {}
                for m_idx, col in enumerate(MONTH_COLS, 1):
                    month_values[col] = pattern_fn(base, m_idx)

                budget = Budget(
                    version_id=version_original.id,
                    cost_center_id=cc.id,
                    account_id=acc.id,
                    notes=None,
                    **month_values,
                )
                db.add(budget)
                db.flush()
                budget_entries[(cc_code, acc_code)] = budget
                budget_count += 1

        print(f"  -> Created {budget_count} budget rows")

        # ---- Actuals (Jan, Feb, Mar 2026) ----
        print("[9/10] Creating actual transactions for Q1 2026...")
        actual_count = 0
        actuals_by_cc_acc_month = {}  # for forecast later

        for month_num in [1, 2, 3]:
            month_col = MONTH_COLS[month_num - 1]
            for cc_code, cc in cost_centers.items():
                for acc_code, acc in accounts.items():
                    budget_entry = budget_entries.get((cc_code, acc_code))
                    if not budget_entry:
                        continue

                    budget_month_val = float(getattr(budget_entry, month_col) or 0)
                    if budget_month_val == 0:
                        continue

                    # Create 3-5 individual transactions per account/cc/month
                    num_transactions = random.randint(3, 5)
                    # Total should be close to budget (variance of +/- 15%)
                    target_total = budget_month_val * (1.0 + random.uniform(-0.15, 0.15))

                    # Split target into random portions
                    portions = [random.random() for _ in range(num_transactions)]
                    portion_sum = sum(portions)
                    portions = [p / portion_sum for p in portions]

                    month_actual_total = Decimal("0")
                    for t_idx, portion in enumerate(portions):
                        amount = round(target_total * portion, 2)
                        day = random.randint(1, 28)
                        vendor = random.choice(VENDORS)

                        actual = Actual(
                            date=date(2026, month_num, day),
                            account_id=acc.id,
                            cost_center_id=cc.id,
                            vendor=vendor,
                            amount=Decimal(str(amount)),
                            description=f"Pagamento ref. {acc.name} - parcela {t_idx + 1}",
                            source=random.choice([ActualSource.erp, ActualSource.manual, ActualSource.excel]),
                        )
                        db.add(actual)
                        month_actual_total += Decimal(str(amount))
                        actual_count += 1

                    key = (cc_code, acc_code)
                    if key not in actuals_by_cc_acc_month:
                        actuals_by_cc_acc_month[key] = {}
                    actuals_by_cc_acc_month[key][month_num] = month_actual_total

        db.flush()
        print(f"  -> Created {actual_count} actual transactions")

        # ---- Forecasts ----
        print("[10/10] Creating forecasts, comments, and audit logs...")
        forecast_count = 0
        for cc_code, cc in cost_centers.items():
            for acc_code, acc in accounts.items():
                key = (cc_code, acc_code)
                actual_months = actuals_by_cc_acc_month.get(key, {})

                # Jan-Mar = actual values, Apr-Dec = average of actuals
                jan_val = actual_months.get(1, Decimal("0"))
                feb_val = actual_months.get(2, Decimal("0"))
                mar_val = actual_months.get(3, Decimal("0"))

                actual_vals = [v for v in [jan_val, feb_val, mar_val] if v > 0]
                avg_actual = sum(actual_vals) / len(actual_vals) if actual_vals else Decimal("0")
                avg_actual = Decimal(str(round(float(avg_actual), 2)))

                month_values = {
                    "jan": jan_val,
                    "feb": feb_val,
                    "mar": mar_val,
                    "apr": avg_actual,
                    "may": avg_actual,
                    "jun": avg_actual,
                    "jul": avg_actual,
                    "aug": avg_actual,
                    "sep": avg_actual,
                    "oct": avg_actual,
                    "nov": avg_actual,
                    "dec": avg_actual,
                }
                total = sum(month_values.values())

                forecast = Forecast(
                    version_id=version_forecast.id,
                    cost_center_id=cc.id,
                    account_id=acc.id,
                    total=total,
                    method=ForecastMethod.linear,
                    created_by=admin_user.id,
                    **month_values,
                )
                db.add(forecast)
                forecast_count += 1

        db.flush()
        print(f"  -> Created {forecast_count} forecast rows")

        # ---- Comments ----
        sample_budgets = list(budget_entries.values())[:10]
        comment_texts = [
            "Valor revisado conforme reuniao de diretoria de 15/01/2026.",
            "Necessario incluir reajuste salarial previsto para marco.",
            "Confirmar com fornecedor o novo contrato de manutencao.",
            "Marketing: campanha de lancamento prevista para junho.",
            "Verificar se o custo de licencas inclui o novo modulo ERP.",
            "Aprovado pelo gestor da area em 10/02/2026.",
            "Despesa de viagem acima do previsto - solicitar justificativa.",
            "Incluir orcamento para treinamento externo no Q2.",
        ]
        comment_users = [
            users["admin@budgetpro.com"],
            users["financeiro@budgetpro.com"],
            users["gestor@budgetpro.com"],
        ]
        for i, text in enumerate(comment_texts):
            if i >= len(sample_budgets):
                break
            comment = Comment(
                budget_id=sample_budgets[i].id,
                user_id=random.choice(comment_users).id,
                text=text,
            )
            db.add(comment)
        print(f"  -> Created {len(comment_texts)} comments")

        # ---- Audit Logs ----
        audit_entries = [
            (admin_user.id, "BudgetVersion", version_original.id, AuditAction.create,
             {"name": "Budget 2026 Original", "status": "draft"}),
            (admin_user.id, "BudgetVersion", version_original.id, AuditAction.approve,
             {"status": "draft -> approved"}),
            (users["financeiro@budgetpro.com"].id, "Budget", sample_budgets[0].id, AuditAction.create,
             {"cost_center": "CC001", "account": "3.1.01"}),
            (users["financeiro@budgetpro.com"].id, "Budget", sample_budgets[1].id, AuditAction.update,
             {"field": "jan", "old": "100000.00", "new": "105000.00"}),
            (admin_user.id, "BudgetVersion", version_forecast.id, AuditAction.create,
             {"name": "Forecast Q1 2026", "status": "draft"}),
            (users["gestor@budgetpro.com"].id, "Budget", sample_budgets[2].id, AuditAction.update,
             {"field": "mar", "old": "80000.00", "new": "82500.00"}),
            (admin_user.id, "Company", company.id, AuditAction.create,
             {"name": "TechCorp S.A."}),
            (users["financeiro@budgetpro.com"].id, "Actual", uuid.uuid4(), AuditAction.create,
             {"action": "excel_import", "rows": 50}),
            (admin_user.id, "User", users["viewer@budgetpro.com"].id, AuditAction.create,
             {"email": "viewer@budgetpro.com", "role": "viewer"}),
            (users["gestor@budgetpro.com"].id, "Budget", sample_budgets[3].id, AuditAction.update,
             {"field": "notes", "new": "Revisado apos reuniao"}),
        ]
        for user_id, entity_type, entity_id, action, changes in audit_entries:
            audit = AuditLog(
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                changes=changes,
            )
            db.add(audit)
        print(f"  -> Created {len(audit_entries)} audit log entries")

        # Commit everything
        db.commit()

        print("\n" + "=" * 60)
        print("Seed completed successfully!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  Company:          1")
        print(f"  Users:            {len(users_data)}")
        print(f"  Departments:      {len(dept_names)}")
        print(f"  Cost Centers:     {len(cc_data)}")
        print(f"  Accounts:         {len(accounts_data)}")
        print(f"  Budget Versions:  2")
        print(f"  Budget Rows:      {budget_count}")
        print(f"  Actual Entries:   {actual_count}")
        print(f"  Forecast Rows:    {forecast_count}")
        print(f"  Comments:         {len(comment_texts)}")
        print(f"  Audit Logs:       {len(audit_entries)}")
        print(f"\nDefault users:")
        for name, email, password, role in users_data:
            print(f"  {email} / {password} ({role.value})")

    except Exception as e:
        db.rollback()
        print(f"\nERROR during seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
