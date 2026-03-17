(() => {
  const STEPS = [
    { id: 1, title: "Шаг 1: Шаблон" },
    { id: 2, title: "Шаг 2: Реквизиты" },
    { id: 3, title: "Шаг 3: Предмет" },
    { id: 4, title: "Шаг 4: Оплата" },
    { id: 5, title: "Шаг 5: Опции" },
  ];

  const TEMPLATE_DEFS = [
    { value: "services", label: "Оказание услуг", title: "ДОГОВОР ОКАЗАНИЯ УСЛУГ", subjectLabel: "Услуги" },
    { value: "work", label: "Подряд (выполнение работ)", title: "ДОГОВОР ПОДРЯДА", subjectLabel: "Работы" },
    { value: "supply", label: "Поставка", title: "ДОГОВОР ПОСТАВКИ", subjectLabel: "Товары" },
    { value: "sale", label: "Купля-продажа", title: "ДОГОВОР КУПЛИ-ПРОДАЖИ", subjectLabel: "Товары" },
    { value: "rent", label: "Аренда", title: "ДОГОВОР АРЕНДЫ", subjectLabel: "Объект аренды" },
    { value: "subrent", label: "Субаренда", title: "ДОГОВОР СУБАРЕНДЫ", subjectLabel: "Объект субаренды" },
    { value: "lease", label: "Лизинг", title: "ДОГОВОР ЛИЗИНГА", subjectLabel: "Предмет лизинга" },
    { value: "agency", label: "Агентский", title: "АГЕНТСКИЙ ДОГОВОР", subjectLabel: "Услуги/обязательства" },
    { value: "commission", label: "Комиссия", title: "ДОГОВОР КОМИССИИ", subjectLabel: "Предмет комиссии" },
    { value: "mandate", label: "Поручение", title: "ДОГОВОР ПОРУЧЕНИЯ", subjectLabel: "Поручение" },
    { value: "loan", label: "Займ", title: "ДОГОВОР ЗАЙМА", subjectLabel: "Сумма займа" },
    { value: "nda", label: "NDA (конфиденциальность)", title: "СОГЛАШЕНИЕ О КОНФИДЕНЦИАЛЬНОСТИ (NDA)", subjectLabel: "Обязательства" },
  ];

  function getTemplateDef() {
    return TEMPLATE_DEFS.find((t) => t.value === state.template) || null;
  }

  const state = {
    step: 1,
    template: "",
    parties: {
      a: { name: "", inn: "", ogrn: "", address: "", bank: "", rs: "", ks: "", bik: "", rep: "", basis: "" },
      b: { name: "", inn: "", ogrn: "", address: "", bank: "", rs: "", ks: "", bik: "", rep: "", basis: "" },
    },
    subject: {
      startDate: "",
      termDays: "",
      items: [{ title: "", qty: 1, price: 0 }],
    },
    payment: {
      type: "",
    },
    options: {
      warranty12: false,
      acceptanceAct: false,
      confidentiality: false,
    },
  };

  const els = {};

  function qs(id) {
    return document.getElementById(id);
  }

  function fmtMoney(n) {
    const num = Number(n);
    if (!Number.isFinite(num)) return "0.00";
    return num.toFixed(2);
  }

  function parseMoney(v) {
    if (typeof v !== "string") return Number(v) || 0;
    const normalized = v.replace(/\s/g, "").replace(",", ".");
    const num = Number(normalized);
    return Number.isFinite(num) ? num : 0;
  }

  function calcTotals() {
    const rows = state.subject.items.map((it) => {
      const qty = Number(it.qty) || 0;
      const price = Number(it.price) || 0;
      return Math.max(0, qty) * Math.max(0, price);
    });
    const total = rows.reduce((a, b) => a + b, 0);
    return { rows, total };
  }

  function addDays(isoDate, days) {
    if (!isoDate) return "";
    const d = new Date(isoDate + "T00:00:00");
    if (Number.isNaN(d.getTime())) return "";
    d.setDate(d.getDate() + (Number(days) || 0));
    const yyyy = String(d.getFullYear()).padStart(4, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }

  function russianDate(isoDate) {
    if (!isoDate) return "";
    const d = new Date(isoDate + "T00:00:00");
    if (Number.isNaN(d.getTime())) return "";
    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const yyyy = d.getFullYear();
    return `${dd}.${mm}.${yyyy}`;
  }

  // Упрощённая сумма прописью (рубли/копейки), без сложной морфологии — достаточно для MVP.
  function sumToWordsRu(amount) {
    const num = Math.round((Number(amount) || 0) * 100) / 100;
    const rub = Math.floor(num);
    const kop = Math.round((num - rub) * 100);
    return `${rub} руб. ${String(kop).padStart(2, "0")} коп.`;
  }

  function missingSpan(label, htmlMode) {
    return htmlMode ? `<span class="missing">${label}</span>` : `__${label}__`;
  }

  function isFilled(v) {
    return String(v || "").trim().length > 0;
  }

  function validate() {
    const problems = [];
    const required = [];

    required.push({ key: "template", ok: isFilled(state.template), label: "Выберите шаблон договора" });
    required.push({ key: "partyAName", ok: isFilled(state.parties.a.name), label: "Укажите Сторону 1 (название)" });
    required.push({ key: "partyBName", ok: isFilled(state.parties.b.name), label: "Укажите Сторону 2 (название)" });

    const hasAtLeastOneItem = state.subject.items.some((it) => isFilled(it.title) && (Number(it.qty) || 0) > 0 && (Number(it.price) || 0) >= 0);
    required.push({ key: "items", ok: hasAtLeastOneItem, label: "Добавьте хотя бы одну позицию предмета договора" });

    required.push({ key: "startDate", ok: isFilled(state.subject.startDate), label: "Укажите дату начала" });
    required.push({ key: "termDays", ok: (Number(state.subject.termDays) || 0) > 0, label: "Укажите срок выполнения (дни)" });
    required.push({ key: "payment", ok: isFilled(state.payment.type), label: "Выберите условия оплаты" });

    for (const r of required) if (!r.ok) problems.push(r.label);
    return { ok: problems.length === 0, problems };
  }

  function buildContractText({ htmlMode } = { htmlMode: true }) {
    const { total } = calcTotals();
    const start = russianDate(state.subject.startDate) || missingSpan("дата начала", htmlMode);
    const term = (Number(state.subject.termDays) || 0) > 0 ? `${Number(state.subject.termDays)} дней` : missingSpan("срок");
    const endIso = addDays(state.subject.startDate, Number(state.subject.termDays) || 0);
    const end = russianDate(endIso) || missingSpan("дата окончания", htmlMode);

    const a = state.parties.a;
    const b = state.parties.b;

    const partyAName = isFilled(a.name) ? a.name : missingSpan("Сторона 1", htmlMode);
    const partyBName = isFilled(b.name) ? b.name : missingSpan("Сторона 2", htmlMode);

    const itemsLines = state.subject.items
      .filter((it) => isFilled(it.title))
      .map((it, idx) => {
        const qty = Number(it.qty) || 0;
        const price = Number(it.price) || 0;
        const sum = qty * price;
        return `${idx + 1}. ${it.title} — ${qty} × ${fmtMoney(price)} = ${fmtMoney(sum)} руб.`;
      });

    const itemsBlock = itemsLines.length ? itemsLines.join("\n") : missingSpan("позиции предмета договора", htmlMode);
    const totalWords = sumToWordsRu(total);

    let paymentText = missingSpan("условия оплаты", htmlMode);
    if (state.payment.type === "prepay30") {
      const pre = total * 0.3;
      const post = total - pre;
      paymentText = `Предоплата 30%: ${fmtMoney(pre)} руб., постоплата 70%: ${fmtMoney(post)} руб.`;
    } else if (state.payment.type === "postpay") {
      paymentText = "Постоплата: оплата производится после исполнения обязательств и подписания документов.";
    } else if (state.payment.type === "equal") {
      paymentText = "Равными платежами: оплата производится равными частями по согласованному графику.";
    }

    const tplDef = getTemplateDef();
    const title = tplDef ? tplDef.title : "ДОГОВОР";
    const subjectLabel = tplDef ? tplDef.subjectLabel : "Позиции";

    const warrantySection = state.options.warranty12
      ? `\n7. Гарантия\n7.1. Гарантия на результат/товар составляет 12 (двенадцать) месяцев с даты исполнения/передачи.\n`
      : "";

    const actSection = state.options.acceptanceAct
      ? `\n6. Приёмка и акт\n6.1. Стороны подписывают акт приёмки (оказанных услуг/переданных товаров) по факту исполнения.\n`
      : "";

    const confSection = state.options.confidentiality
      ? `\n8. Конфиденциальность\n8.1. Стороны обязуются не раскрывать конфиденциальную информацию, полученную в рамках исполнения договора.\n`
      : "";

    return [
      title,
      "",
      `г. ________    "${new Date().getDate()}" ________ ${new Date().getFullYear()} г.`,
      "",
      `1. Стороны`,
      `1.1. ${partyAName} (далее — "Сторона 1") и ${partyBName} (далее — "Сторона 2") заключили настоящий договор.`,
      "",
      `2. Предмет договора`,
      `2.1. ${subjectLabel}:`,
      `${itemsBlock}`,
      "",
      `3. Сроки`,
      `3.1. Дата начала: ${start}. Срок выполнения: ${term}.`,
      `3.2. Дата окончания (расчётная): ${end}.`,
      "",
      `4. Стоимость`,
      `4.1. Общая стоимость: ${fmtMoney(total)} руб. (${totalWords}).`,
      "",
      `5. Порядок оплаты`,
      `5.1. ${paymentText}`,
      actSection ? actSection.trimEnd() : "",
      warrantySection ? warrantySection.trimEnd() : "",
      confSection ? confSection.trimEnd() : "",
      `\n9. Реквизиты и подписи`,
      `Сторона 1: ${isFilled(a.name) ? a.name : "________"}`,
      `Сторона 2: ${isFilled(b.name) ? b.name : "________"}`,
    ]
      .filter((x) => x !== "")
      .join("\n");
  }

  function buildContractPayload() {
    const totals = calcTotals();
    const endIso = addDays(state.subject.startDate, Number(state.subject.termDays) || 0);
    return {
      template: state.template,
      title: (getTemplateDef() ? getTemplateDef().title : "ДОГОВОР"),
      parties: state.parties,
      subject: {
        startDate: state.subject.startDate,
        termDays: Number(state.subject.termDays) || 0,
        endDate: endIso,
        items: state.subject.items.map((it) => ({
          title: String(it.title || "").trim(),
          qty: Number(it.qty) || 0,
          price: Number(it.price) || 0,
        })),
        total: totals.total,
      },
      payment: state.payment,
      options: state.options,
      text_plain: buildContractText({ htmlMode: false }),
    };
  }

  function renderStepPills() {
    els.stepPills.innerHTML = STEPS.map((s) => {
      const active = s.id === state.step ? "active" : "";
      return `<div class="step-pill ${active}" data-step="${s.id}" title="${s.title}">${s.id}</div>`;
    }).join("");

    els.stepPills.querySelectorAll("[data-step]").forEach((pill) => {
      pill.addEventListener("click", () => {
        state.step = Number(pill.getAttribute("data-step"));
        render();
      });
    });
  }

  function fieldWrap({ id, label, required = false, type = "text", value = "", placeholder = "", hint = "", options = null }) {
    const cls = ["field", required ? "required" : ""].filter(Boolean).join(" ");
    if (options) {
      return `
        <div class="${cls}" data-field="${id}">
          <label for="${id}">${label}</label>
          <select id="${id}">
            ${options.map((o) => `<option value="${o.value}" ${String(o.value) === String(value) ? "selected" : ""}>${o.label}</option>`).join("")}
          </select>
          ${hint ? `<div class="hint">${hint}</div>` : ""}
        </div>
      `;
    }
    if (type === "textarea") {
      return `
        <div class="${cls}" data-field="${id}">
          <label for="${id}">${label}</label>
          <textarea id="${id}" placeholder="${placeholder}">${value ?? ""}</textarea>
          ${hint ? `<div class="hint">${hint}</div>` : ""}
        </div>
      `;
    }
    return `
      <div class="${cls}" data-field="${id}">
        <label for="${id}">${label}</label>
        <input id="${id}" type="${type}" value="${value ?? ""}" placeholder="${placeholder}">
        ${hint ? `<div class="hint">${hint}</div>` : ""}
      </div>
    `;
  }

  function renderStep() {
    if (state.step === 1) {
      els.stepContainer.innerHTML = `
        ${fieldWrap({
          id: "template",
          label: "Шаблон договора",
          required: true,
          options: [
            { value: "", label: "— выберите —" },
            ...TEMPLATE_DEFS.map((t) => ({ value: t.value, label: t.label })),
          ],
          value: state.template,
          hint: "Шаблон влияет на заголовок и текстовые формулировки (в MVP — базово).",
        })}
      `;

      qs("template").addEventListener("change", (e) => {
        state.template = e.target.value;
        renderPreviewAndValidation();
      });
      return;
    }

    if (state.step === 2) {
      els.stepContainer.innerHTML = `
        <div class="grid-2">
          <div>
            <h3 style="margin-bottom:8px; font-size:1rem;">Сторона 1</h3>
            ${fieldWrap({ id: "a_name", label: "Название", required: true, value: state.parties.a.name, placeholder: "ООО «Ромашка» / ИП Иванов И.И." })}
            ${fieldWrap({ id: "a_inn", label: "ИНН", value: state.parties.a.inn })}
            ${fieldWrap({ id: "a_ogrn", label: "ОГРН/ОГРНИП", value: state.parties.a.ogrn })}
            ${fieldWrap({ id: "a_address", label: "Адрес", type: "textarea", value: state.parties.a.address })}
          </div>
          <div>
            <h3 style="margin-bottom:8px; font-size:1rem;">Сторона 2</h3>
            ${fieldWrap({ id: "b_name", label: "Название", required: true, value: state.parties.b.name, placeholder: "ООО «Лютик» / ИП Петров П.П." })}
            ${fieldWrap({ id: "b_inn", label: "ИНН", value: state.parties.b.inn })}
            ${fieldWrap({ id: "b_ogrn", label: "ОГРН/ОГРНИП", value: state.parties.b.ogrn })}
            ${fieldWrap({ id: "b_address", label: "Адрес", type: "textarea", value: state.parties.b.address })}
          </div>
        </div>
      `;

      const bind = (id, getter, setter) => {
        qs(id).addEventListener("input", (e) => {
          setter(e.target.value);
          renderPreviewAndValidation();
        });
      };

      bind("a_name", () => state.parties.a.name, (v) => (state.parties.a.name = v));
      bind("a_inn", () => state.parties.a.inn, (v) => (state.parties.a.inn = v));
      bind("a_ogrn", () => state.parties.a.ogrn, (v) => (state.parties.a.ogrn = v));
      bind("a_address", () => state.parties.a.address, (v) => (state.parties.a.address = v));

      bind("b_name", () => state.parties.b.name, (v) => (state.parties.b.name = v));
      bind("b_inn", () => state.parties.b.inn, (v) => (state.parties.b.inn = v));
      bind("b_ogrn", () => state.parties.b.ogrn, (v) => (state.parties.b.ogrn = v));
      bind("b_address", () => state.parties.b.address, (v) => (state.parties.b.address = v));
      return;
    }

    if (state.step === 3) {
      const { rows, total } = calcTotals();
      const itemRowsHtml = state.subject.items
        .map((it, idx) => {
          const lineSum = rows[idx] ?? 0;
          return `
            <div class="items-row" data-idx="${idx}">
              <input class="it_title" placeholder="Название услуги/товара" value="${it.title ?? ""}">
              <input class="it_qty" type="number" min="0" step="1" value="${Number(it.qty) || 0}">
              <input class="it_price" type="number" min="0" step="0.01" value="${Number(it.price) || 0}">
              <input class="it_sum" type="text" value="${fmtMoney(lineSum)}" disabled>
              <button class="icon-btn it_del" title="Удалить" ${state.subject.items.length <= 1 ? "disabled" : ""}>×</button>
            </div>
          `;
        })
        .join("");

      els.stepContainer.innerHTML = `
        <div style="display:flex; justify-content: space-between; align-items:center; gap:10px; margin-bottom:10px;">
          <div>
            <div style="font-weight:700;">Позиции</div>
            <div class="hint">В MVP — ручной ввод. Каталог можно подключить позже.</div>
          </div>
          <button class="btn" id="btnAddItem">+ Добавить</button>
        </div>
        <div class="items">
          <div class="items-header">
            <div>Наименование</div><div>Кол-во</div><div>Цена</div><div>Сумма</div><div></div>
          </div>
          <div id="itemsBody">${itemRowsHtml}</div>
        </div>

        <div class="grid-2" style="margin-top:12px;">
          ${fieldWrap({ id: "startDate", label: "Дата начала", required: true, type: "date", value: state.subject.startDate })}
          ${fieldWrap({ id: "termDays", label: "Срок (дней)", required: true, type: "number", value: state.subject.termDays, placeholder: "Например: 10" })}
        </div>

        <div class="totals">
          <div><span>Итого</span> <b>${fmtMoney(total)} руб.</b></div>
          <div><span>Прописью (MVP)</span> <span>${sumToWordsRu(total)}</span></div>
          <div><span>Дата окончания (расчётная)</span> <span>${russianDate(addDays(state.subject.startDate, Number(state.subject.termDays) || 0)) || "—"}</span></div>
        </div>
      `;

      qs("btnAddItem").addEventListener("click", () => {
        state.subject.items.push({ title: "", qty: 1, price: 0 });
        render();
      });

      const itemsBody = qs("itemsBody");
      itemsBody.querySelectorAll(".items-row").forEach((row) => {
        const idx = Number(row.getAttribute("data-idx"));
        row.querySelector(".it_title").addEventListener("input", (e) => {
          state.subject.items[idx].title = e.target.value;
          renderPreviewAndValidation();
        });
        row.querySelector(".it_qty").addEventListener("input", (e) => {
          state.subject.items[idx].qty = Number(e.target.value) || 0;
          render();
        });
        row.querySelector(".it_price").addEventListener("input", (e) => {
          state.subject.items[idx].price = Number(e.target.value) || 0;
          render();
        });
        row.querySelector(".it_del").addEventListener("click", () => {
          if (state.subject.items.length <= 1) return;
          state.subject.items.splice(idx, 1);
          render();
        });
      });

      qs("startDate").addEventListener("change", (e) => {
        state.subject.startDate = e.target.value;
        render();
      });
      qs("termDays").addEventListener("input", (e) => {
        state.subject.termDays = e.target.value;
        render();
      });
      return;
    }

    if (state.step === 4) {
      els.stepContainer.innerHTML = `
        ${fieldWrap({
          id: "paymentType",
          label: "Условия оплаты",
          required: true,
          options: [
            { value: "", label: "— выберите —" },
            { value: "prepay30", label: "Предоплата 30%" },
            { value: "postpay", label: "Постоплата" },
            { value: "equal", label: "Равными платежами" },
          ],
          value: state.payment.type,
        })}
        <div class="hint">В превью автоматически появится соответствующий пункт оплаты.</div>
      `;
      qs("paymentType").addEventListener("change", (e) => {
        state.payment.type = e.target.value;
        renderPreviewAndValidation();
      });
      return;
    }

    if (state.step === 5) {
      const chk = (id, label, value) => `
        <label style="display:flex; gap:10px; align-items:center; padding:10px 12px; border:1px solid var(--border); border-radius:14px; background:#fff; cursor:pointer; margin-bottom:10px;">
          <input id="${id}" type="checkbox" ${value ? "checked" : ""} style="width:18px; height:18px;">
          <span style="font-weight:600;">${label}</span>
        </label>
      `;
      els.stepContainer.innerHTML = `
        ${chk("optWarranty", "Гарантия 12 мес.", state.options.warranty12)}
        ${chk("optAct", "Акт приёмки", state.options.acceptanceAct)}
        ${chk("optConf", "Конфиденциальность", state.options.confidentiality)}
        <div class="hint">Разделы будут добавляться/убираться в тексте договора автоматически.</div>
      `;

      qs("optWarranty").addEventListener("change", (e) => {
        state.options.warranty12 = e.target.checked;
        renderPreviewAndValidation();
      });
      qs("optAct").addEventListener("change", (e) => {
        state.options.acceptanceAct = e.target.checked;
        renderPreviewAndValidation();
      });
      qs("optConf").addEventListener("change", (e) => {
        state.options.confidentiality = e.target.checked;
        renderPreviewAndValidation();
      });
      return;
    }
  }

  function setInvalidFields() {
    document.querySelectorAll("[data-field]").forEach((el) => el.classList.remove("invalid"));

    // Помечаем только те поля, которые реально видимы на текущем шаге
    const invalid = new Set();

    if (!isFilled(state.template)) invalid.add("template");
    if (!isFilled(state.parties.a.name)) invalid.add("a_name");
    if (!isFilled(state.parties.b.name)) invalid.add("b_name");

    const hasAtLeastOneItem = state.subject.items.some(
      (it) => isFilled(it.title) && (Number(it.qty) || 0) > 0 && (Number(it.price) || 0) >= 0
    );
    if (!hasAtLeastOneItem) invalid.add("items");

    if (!isFilled(state.subject.startDate)) invalid.add("startDate");
    if ((Number(state.subject.termDays) || 0) <= 0) invalid.add("termDays");
    if (!isFilled(state.payment.type)) invalid.add("paymentType");

    const visibleFieldIdsByStep = {
      1: ["template"],
      2: ["a_name", "b_name"],
      3: ["items", "startDate", "termDays"],
      4: ["paymentType"],
      5: [],
    };

    const visible = visibleFieldIdsByStep[state.step] || [];
    for (const id of visible) {
      if (!invalid.has(id)) continue;

      // items — подсветим блок целиком
      if (id === "items") {
        const items = document.querySelector(".items");
        if (items) items.style.boxShadow = "0 0 0 4px rgba(249,65,68,0.10)";
        if (items) items.style.borderColor = "rgba(249,65,68,0.75)";
        continue;
      } else {
        const wrap = document.querySelector(`[data-field="${id}"]`);
        if (wrap) wrap.classList.add("invalid");
      }
    }

    // Убираем подсветку items если всё ок
    if (!invalid.has("items")) {
      const items = document.querySelector(".items");
      if (items) {
        items.style.boxShadow = "";
        items.style.borderColor = "";
      }
    }

    const { ok, problems } = validate();
    els.validationHint.textContent = ok ? "Все обязательные поля заполнены — можно создавать PDF." : `Заполните: ${problems.join("; ")}`;
  }

  function renderPreviewAndValidation() {
    const text = buildContractText({ htmlMode: true });
    els.previewText.innerHTML = text;

    const v = validate();
    els.btnPdf.disabled = !v.ok;
    setInvalidFields();
  }

  function go(delta) {
    state.step = Math.min(5, Math.max(1, state.step + delta));
    render();
  }

  async function createPdf() {
    const v = validate();
    if (!v.ok) return;

    const payload = {
      filename: "contract.pdf",
      contract: buildContractPayload(),
    };

    els.btnPdf.disabled = true;
    els.btnPdf.textContent = "Генерация...";
    try {
      const res = await fetch("/api/contracts/generate-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "Ошибка генерации PDF");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "contract.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(String(e.message || e));
    } finally {
      els.btnPdf.textContent = "Создать PDF";
      renderPreviewAndValidation();
    }
  }

  async function copyText() {
    const text = buildContractText({ htmlMode: false });
    try {
      await navigator.clipboard.writeText(text);
      els.btnCopy.textContent = "Скопировано";
      setTimeout(() => (els.btnCopy.textContent = "Копировать текст"), 900);
    } catch {
      // fallback
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      els.btnCopy.textContent = "Скопировано";
      setTimeout(() => (els.btnCopy.textContent = "Копировать текст"), 900);
    }
  }

  function render() {
    renderStepPills();
    renderStep();

    els.btnPrev.disabled = state.step === 1;
    // На последнем шаге "Далее" превращаем в "Готово" (чтобы не выглядело как баг)
    if (state.step === 5) {
      els.btnNext.disabled = false;
      els.btnNext.textContent = "Готово";
    } else {
      els.btnNext.disabled = false;
      els.btnNext.textContent = "Далее →";
    }

    renderPreviewAndValidation();
  }

  function init() {
    els.stepPills = qs("stepPills");
    els.stepContainer = qs("stepContainer");
    els.previewText = qs("previewText");
    els.btnPrev = qs("btnPrev");
    els.btnNext = qs("btnNext");
    els.btnPdf = qs("btnPdf");
    els.btnCopy = qs("btnCopy");
    els.validationHint = qs("validationHint");

    els.btnPrev.addEventListener("click", () => go(-1));
    els.btnNext.addEventListener("click", () => {
      if (state.step === 5) {
        // Ничего "дальше" нет — просто фокусируем пользователя на превью/PDF
        els.previewText.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
      go(1);
    });
    els.btnPdf.addEventListener("click", createPdf);
    els.btnCopy.addEventListener("click", copyText);

    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

