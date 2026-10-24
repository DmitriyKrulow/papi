import React, { useState, useEffect } from "react"

interface ScheduleItem {
  id: number; name: string; scheduled_date: string; check_category: string; check_type: string;
  status: "scheduled" | "in_progress" | "completed" | "cancelled" | "overdue";
  target_type?: string; target_id?: number; target_name?: string; responsible_id?: number; responsible_name?: string; comment?: string;
}

interface CalendarData { calendar: Record<string, ScheduleItem[]>; total: number; }
interface UpcomingCheck { id: number; name: string; target_name?: string; scheduled_date: string; days_until: number; responsible_id?: number; }
interface ScheduleStats { scheduled: number; in_progress: number; completed: number; overdue: number; rooms_checked_last_6_months: number; total_rooms: number; coverage_percent: number; }
interface CheckTypeCategory { id: string; name: string; types: string[]; }
interface TypesData { categories: CheckTypeCategory[]; type_labels: Record<string, string>; }
interface AutoGeneratePayload { category: string; check_type: string; target_type: string; months: number; start_date?: string; }
interface EditSchedulePayload { scheduled_date?: string; status?: string; comment?: string; responsible_id?: number; }
interface AutoGenCategory { id: string; name: string; check_type: string; target_type: string; }

const CHECK_TYPE_LABELS: Record<string, string> = {
  room: "Проверка помещения", flash_drive: "Проверка флеш-накопителей", token: "Проверка электронных токенов",
  signature: "Проверка ЭЦП", seal_stamp: "Проверка печатей", vehicle: "Проверка автомобилей",
  fire_extinguisher: "Проверка огнетушителей", ppe: "Проверка СИЗ", security_drill: "Учения по ИБ",
  fire_safety: "Учения по пожарной безопасности", employee_appearance: "Проверка внешнего вида сотрудников",
};
const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  scheduled: { label: "Запланировано", color: "text-blue-700", bg: "bg-blue-100" },
  in_progress: { label: "В процессе", color: "text-yellow-700", bg: "bg-yellow-100" },
  completed: { label: "Выполнено", color: "text-green-700", bg: "bg-green-100" },
  cancelled: { label: "Отменено", color: "text-gray-700", bg: "bg-gray-100" },
  overdue: { label: "Просрочено", color: "text-red-700", bg: "bg-red-100" },
};
const MONTHS_RU = ["Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"];
const DAYS_RU = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"];
function getDaysInMonth(y: number, m: number){return new Date(y,m+1,0).getDate();}
function getFirstDayOfMonth(y: number, m: number){const d=new Date(y,m,1).getDay();return d===0?6:d-1;}
function getStatusConfig(s: string){return STATUS_CONFIG[s]||{label:s,color:"text-gray-700",bg:"bg-gray-100"};}

function SchedulePage() {
  const now = new Date();
  const [currentMonth, setCurrentMonth] = useState(now.getMonth());
  const [currentYear, setCurrentYear] = useState(now.getFullYear());
  const [calendarData, setCalendarData] = useState<ScheduleItem[]>([]);
  const [upcomingChecks, setUpcomingChecks] = useState<UpcomingCheck[]>([]);
  const [stats, setStats] = useState<ScheduleStats | null>(null);
  const [typesData, setTypesData] = useState<TypesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState("");
  const [filterType, setFilterType] = useState("");
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedItems, setSelectedItems] = useState<ScheduleItem[]>([]);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAutoGenerateModal, setShowAutoGenerateModal] = useState(false);
  const [editData, setEditData] = useState<EditSchedulePayload>({scheduled_date:"",status:"scheduled",comment:"",responsible_id:undefined});
  const [autoGenData, setAutoGenData] = useState<AutoGeneratePayload>({category:"room",check_type:"room",target_type:"room",months:6,start_date:new Date().toISOString().split("T")[0]});
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [autoGenCategories, setAutoGenCategories] = useState<AutoGenCategory[]>([]);

  useEffect(()=>{try{const u=JSON.parse(localStorage.getItem("user")||"{}");setIsAdmin(u.role==="admin"||u.is_admin===true)}catch{setIsAdmin(false)}},[]);

  useEffect(()=>{if(isAdmin){const token=localStorage.getItem("token");fetch("/api/inventory-schedule/auto-generate-categories",{headers:token?{Authorization:"Bearer "+token}:{} }).then(r=>r.json()).then(d=>{if(d.categories)setAutoGenCategories(d.categories)}).catch(()=>{})}},[isAdmin]);

  const fetchData = async ()=>{
    setLoading(true); setError(null);
    try{
      const token=localStorage.getItem("token"); const h:Record<string,string>={}; if(token)h.Authorization="Bearer "+token;
      const[cr,ur,sr,tr]=await Promise.all([
        fetch("/api/inventory-schedule/calendar?month="+(currentMonth+1)+"&year="+currentYear+(filterCategory?"&check_category="+filterCategory:"")+(filterType?"&check_type="+filterType:""),{headers:h}),
        fetch("/api/inventory-schedule/upcoming?days_ahead=30",{headers:h}),
        fetch("/api/inventory-schedule/stats",{headers:h}),
        fetch("/api/inventory-schedule/types",{headers:h}),
      ]);
      if(!cr.ok||!ur.ok||!sr.ok||!tr.ok)throw new Error("Ошибка загрузки");
      const[cd,ud,sd,td]=await Promise.all([cr.json() as Promise<CalendarData>,ur.json() as Promise<{upcoming:UpcomingCheck[];total:number}>,sr.json() as Promise<ScheduleStats>,tr.json() as Promise<TypesData>]);
      const items:ScheduleItem[]=[]; if(cd.calendar)Object.values(cd.calendar).forEach(di=>items.push(...Array.isArray(di)?di:[]));
      setCalendarData(items); setUpcomingChecks(Array.isArray(ud.upcoming)?ud.upcoming:[]); setStats(sd); setTypesData(td);
    }catch(e:any){setError(e.message||"Ошибка")}finally{setLoading(false)}
  };
  useEffect(()=>{fetchData()},[currentMonth,currentYear,filterCategory,filterType]);

  const daysInMonth=getDaysInMonth(currentYear,currentMonth); const firstDay=getFirstDayOfMonth(currentYear,currentMonth);
  const pmN=currentMonth===0?11:currentMonth-1, pmY=currentMonth===0?currentYear-1:currentYear, pmD=getDaysInMonth(pmY,pmN);
  const calDays:{day:number;cm:boolean;ds?:string;items?:ScheduleItem[]}[]=[];
  for(let i=firstDay-1;i>=0;i--)calDays.push({day:pmD-i,cm:false});
  for(let d=1;d<=daysInMonth;d++){const ds=currentYear+"-"+String(currentMonth+1).padStart(2,"0")+"-"+String(d).padStart(2,"0");const items=calendarData.filter((item:ScheduleItem)=>item.scheduled_date.startsWith(ds));calDays.push({day:d,cm:true,ds,items});}
  const tc=calDays.length,rem=42-tc; for(let i=1;i<=rem;i++)calDays.push({day:i,cm:false});

  const handleDateClick=(day:number)=>{const ds=currentYear+"-"+String(currentMonth+1).padStart(2,"0")+"-"+String(day).padStart(2,"0");const items=calendarData.filter((item:ScheduleItem)=>item.scheduled_date.startsWith(ds));setSelectedDate(ds);setSelectedItems(items);if(items.length>0)setEditData({scheduled_date:ds,status:items[0].status,comment:items[0].comment||"",responsible_id:items[0].responsible_id});};
  const handleSaveEdit=async()=>{if(selectedDate&&selectedItems.length>0){setSaving(true);try{await Promise.all(selectedItems.map((it:ScheduleItem)=>fetch("/api/inventory-schedule/"+it.id,{method:"PUT",headers:{"Content-Type":"application/json","Authorization":"Bearer "+localStorage.getItem("token")},body:JSON.stringify({scheduled_date:editData.scheduled_date||selectedDate,status:editData.status,comment:editData.comment,responsible_id:editData.responsible_id})})));setShowEditModal(false);fetchData()}catch(e:any){alert("Ошибка сохранения: "+(e.message||"неизвестная ошибка"))}finally{setSaving(false)}}};
  const handleAutoGenerate=async()=>{setGenerating(true);try{const r=await fetch("/api/inventory-schedule/auto-generate",{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+localStorage.getItem("token")},body:JSON.stringify(autoGenData)});if(!r.ok){const e=await r.json();throw new Error(e.detail||"Ошибка генерации")}setShowAutoGenerateModal(false);fetchData()}catch(e:any){alert("Ошибка генерации: "+(e.message||"неизвестная ошибка"))}finally{setGenerating(false)}};
  const prevMonth=()=>{if(currentMonth===0){setCurrentMonth(11);setCurrentYear(currentYear-1)}else{setCurrentMonth(currentMonth-1)}};
  const nextMonth=()=>{if(currentMonth===11){setCurrentMonth(0);setCurrentYear(currentYear+1)}else{setCurrentMonth(currentMonth+1)}};
  const goToday=()=>{setCurrentMonth(now.getMonth());setCurrentYear(now.getFullYear())};
  const totalItems=stats?.scheduled+stats?.in_progress+stats?.completed+stats?.overdue||0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-graphite-950">
      <main className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div><h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100">Расписание</h1></div>
          {(isAdmin &&           <button onClick={()=>setShowAutoGenerateModal(true)} className="btn-primary-modern">Автогенерация</button>)}
        </div>
        {(error && <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg text-sm" role="alert">{error}</div>)}
        {(stats && <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="card-modern p-5">
            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Всего</p><p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{totalItems}</p></div>
          <div className="card-modern p-5">
            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Запланировано</p><p className="text-2xl font-bold text-blue-600 mt-1">{stats.scheduled}</p></div>
          <div className="card-modern p-5">
            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Выполнено</p><p className="text-2xl font-bold text-green-600 mt-1">{stats.completed}</p></div>
          <div className="card-modern p-5">
            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Просрочено</p><p className="text-2xl font-bold text-red-600 mt-1">{stats.overdue}</p></div>
        </div>)}
        <div className="card-modern p-5">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <button onClick={prevMonth} className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition text-sm">Назад</button>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{MONTHS_RU[currentMonth]} {currentYear}</h2>
              <button onClick={nextMonth} className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition text-sm">Вперёд</button>
              <button onClick={goToday} className="px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition text-sm">Сегодня</button>
            </div>
            <div className="flex gap-2">
              <select value={filterCategory} onChange={e=>setFilterCategory(e.target.value)} className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
                <option value="">Все категории</option>
                {typesData?.categories && Array.isArray(typesData.categories) && typesData.categories.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <select value={filterType} onChange={e=>setFilterType(e.target.value)} className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
                <option value="">Все типы</option>
                {typesData?.type_labels && Array.isArray(Object.entries(typesData.type_labels)) && Object.entries(typesData.type_labels).map(([k,v])=><option key={k} value={k}>{v}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-7 gap-1">
            {DAYS_RU.map((d, i) => (
              <div key={i} className="text-center text-xs font-medium text-gray-500 dark:text-gray-400 py-2">{d}</div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {Array.isArray(calDays) && calDays.map((cd, i) => (
              <div key={i} onClick={() => cd.cm && handleDateClick(cd.day)} className="min-h-[80px] p-1 rounded-lg border transition cursor-pointer">
                <div className="text-sm">{cd.day}</div>
                {cd.items !== undefined && cd.items.map((it) => (
                  <div key={it.id} className="text-xs mt-0.5 px-1 py-0.5 rounded truncate" title={it.name}>
                    {it.name}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
        <div className="card-modern p-5">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Предстоящие проверки</h3>
          {upcomingChecks.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-sm">Нет предстоящих проверок</p>
          ) : (
            <div className="space-y-2">
              {Array.isArray(upcomingChecks) && upcomingChecks.map((uc) => (
                <div key={uc.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{uc.name}</p>
                    {uc.target_name !== undefined && <p className="text-xs text-gray-500 dark:text-gray-400">{uc.target_name}</p>}
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-red-600">{uc.days_until} дн.</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        {(showEditModal && <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Редактирование</h3>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Дата</label>
                <input type="date" value={editData.scheduled_date} onChange={e=>setEditData({...editData,scheduled_date:e.target.value})} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
              </div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Статус</label>
                <select value={editData.status} onChange={e=>setEditData({...editData,status:e.target.value})} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
                  <option value="scheduled">Запланировано</option>
                  <option value="completed">Выполнено</option>
                  <option value="cancelled">Отменено</option>
                </select>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Комментарий</label>
                <textarea value={editData.comment} onChange={e=>setEditData({...editData,comment:e.target.value})} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" rows={3} />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button onClick={handleSaveEdit} disabled={saving} className="btn-primary-modern flex-1">{saving?<span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>:<span>Сохранить</span>}</button>
              <button onClick={()=>setShowEditModal(false)} className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition text-sm">Отмена</button>
            </div>
          </div>
        </div>)}
        {(showAutoGenerateModal && <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Автогенерация расписания</h3>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Категория</label>
                <select value={autoGenData.category} onChange={e=>{const cat=autoGenCategories.find(c=>c.id===e.target.value);if(cat)setAutoGenData({...autoGenData,category:cat.id,check_type:cat.check_type,target_type:cat.target_type})}} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
                  {autoGenCategories.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Месяцев</label>
                <select value={autoGenData.months} onChange={e=>setAutoGenData({...autoGenData,months:parseInt(e.target.value)})} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
                  <option value="3">3 месяца</option>
                  <option value="6">6 месяцев</option>
                  <option value="12">12 месяцев</option>
                </select>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Дата начала</label>
                <input type="date" value={autoGenData.start_date} onChange={e=>setAutoGenData({...autoGenData,start_date:e.target.value})} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button onClick={handleAutoGenerate} disabled={generating} className="btn-primary-modern flex-1">{generating?<span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>:<span>Создать</span>}</button>
              <button onClick={()=>setShowAutoGenerateModal(false)} className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition text-sm">Отмена</button>
            </div>
          </div>
        </div>)}
      </main>
    </div>
  );
};

export default SchedulePage;
