import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  ClipboardList, 
  LayoutDashboard, 
  Map as MapIcon, 
  ChevronRight,
  User,
  LogOut,
  Search,
  Trash2,
  Menu,
  X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import DistrictMap from './components/DistrictMap';
import ReportForm from './components/ReportForm';
import ReportsAnalytics from './components/ReportsAnalytics';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

function App() {
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [showReportForm, setShowReportForm] = useState(false);
  const [districts, setDistricts] = useState([]);
  const [churches, setChurches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('map'); 
  
  // Advanced Filtering State
  const [filterPastor, setFilterPastor] = useState('');
  const [filterDistrict, setFilterDistrict] = useState('');
  const [filterChurchDistrict, setFilterChurchDistrict] = useState('');
  const [showBoundaries, setShowBoundaries] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const { data: distData } = await supabase.from('ezc_districts').select('*');
      const { data: churchData } = await supabase.from('ezc_churches').select('*');
      setDistricts(distData || []);
      setChurches(churchData || []);
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Combined Filtering Logic with Search
  const filteredChurches = churches.filter(c => {
    const s = searchTerm.toLowerCase();
    const matchSearch = !searchTerm || 
                        c.name.toLowerCase().includes(s) || 
                        c.pastor_name?.toLowerCase().includes(s) ||
                        c.district_name?.toLowerCase().includes(s);
    
    const matchPastor = !filterPastor || c.pastor_name === filterPastor;
    const matchDistrictLink = !filterDistrict || c.district_id === filterDistrict;
    const matchChurchDistrict = !filterChurchDistrict || c.district_name === filterChurchDistrict;
    
    return matchSearch && matchPastor && matchDistrictLink && matchChurchDistrict;
  });

  const filteredDistricts = districts.filter(d => {
    const s = searchTerm.toLowerCase();
    const matchSearch = !searchTerm || d.name.toLowerCase().includes(s);
    
    const matchDistrict = !filterDistrict || d.id === filterDistrict;
    const districtChurch = churches.find(c => c.id === d.church_id);
    const matchPastor = !filterPastor || (districtChurch && districtChurch.pastor_name === filterPastor);
    
    return matchSearch && matchDistrict && matchPastor;
  });

  const pastorDistricts = filterPastor 
    ? districts.filter(d => churches.some(c => c.id === d.church_id && c.pastor_name === filterPastor))
    : [];

  return (
    <div className="flex h-screen bg-[#EFF3EE] text-[#1A2E1A] overflow-hidden font-body selection:bg-[#2E7D32] selection:text-white relative">
      {/* Sidebar Mobile Backdrop */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsSidebarOpen(false)}
            className="fixed inset-0 bg-[#1A2E1A]/40 backdrop-blur-sm z-40 md:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar - Institutional Edge-to-Edge */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-72 bg-white border-r-2 border-[#2E7D32] flex flex-col overflow-hidden transition-transform duration-300 ease-in-out
        md:relative md:translate-x-0 md:w-80 md:z-20
        ${isSidebarOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full md:translate-x-0'}
      `}>
        {/* Pinned Header - Elite Brand Section */}
        <div className="p-6 premium-header-gradient authority-border-bottom shrink-0 shadow-sm relative flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 flex items-center justify-center shrink-0 logo-floating md:w-16 md:h-16">
              <img src="/sda_logo.svg" alt="SDA Logo" className="w-full h-full object-contain" />
            </div>
            
            <div className="gold-divider hidden xs:block"></div>

            <div className="overflow-hidden">
              <h1 className="text-lg md:text-xl font-black text-[#1A2E1A] leading-none tracking-tight">
                EZC <span className="text-[#2E7D32]">PASTORS</span>
              </h1>
              <p className="text-[9px] md:text-[11px] text-[#2E7D32] font-black uppercase tracking-[0.2em]">Conference GIS Intel</p>
            </div>
          </div>

          <button 
            onClick={() => setIsSidebarOpen(false)}
            className="p-2 text-[#2E7D32] hover:bg-[#E8F0E8] rounded-full transition-colors md:hidden"
          >
            <X size={24} />
          </button>
        </div>

        {/* Scrollable Navigation & Filters */}
        <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-8 bg-[#F8FAF8]/30">
          <nav className="space-y-2">
            {[
              { id: 'map', icon: MapIcon, label: 'Territory Map' },
              { id: 'reports', icon: ClipboardList, label: 'Pastoral Reports' },
              { id: 'analytics', icon: BarChart3, label: 'Analytics' },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  if (window.innerWidth < 768) setIsSidebarOpen(false);
                }}
                className={`w-full flex items-center gap-4 px-5 py-4 rounded-lg transition-all duration-300 border-l-[6px] ${
                  activeTab === item.id 
                    ? 'bg-white text-[#2E7D32] border-[#2E7D32] font-black uppercase tracking-widest text-[12px] shadow-sm' 
                    : 'text-[#1A2E1A]/70 hover:bg-white hover:text-[#2E7D32] border-transparent font-bold text-[11px]'
                }`}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          <div className="space-y-6 pt-6 border-t-2 border-[#F0F4F0]">
            <div className="space-y-3">
              <p className="text-[10px] font-black text-[#2E7D32] uppercase tracking-[0.3em] px-1">Mission Visibility</p>
              <button 
                onClick={() => setShowBoundaries(!showBoundaries)}
                className={`w-full flex items-center justify-between p-4 rounded-xl border-2 transition-all duration-300 ${
                  showBoundaries 
                    ? 'bg-[#E8F0E8] border-[#2E7D32] text-[#2E7D32] shadow-sm' 
                    : 'bg-white border-[#F0F4F0] text-[#1A2E1A]/40'
                }`}
              >
                <span className="text-[11px] font-black uppercase tracking-tight">Boundaries</span>
                <div className={`w-10 h-6 rounded-full relative transition-colors ${showBoundaries ? 'bg-[#2E7D32]' : 'bg-[#E8F0E8]'}`}>
                    <motion.div 
                        animate={{ x: showBoundaries ? 16 : 0 }}
                        className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow-sm"
                    />
                </div>
              </button>
            </div>

            <div className="space-y-4">
              <p className="text-[10px] font-black text-[#2E7D32] uppercase tracking-[0.3em] px-1">Intel Filters</p>
              <div className="space-y-2">
                <label className="text-[11px] font-black text-[#1A2E1A] px-1 block uppercase">Shepherd Context</label>
                <select 
                  value={filterPastor}
                  onChange={(e) => {setFilterPastor(e.target.value); setFilterDistrict('');}}
                  className="w-full bg-white border-2 border-[#2E7D32] rounded-lg p-4 text-xs text-[#1A2E1A] font-black outline-none focus:border-[#F9A825]"
                >
                  <option value="">All Shepherds</option>
                  {[...new Set(churches.map(c => c.pastor_name))].filter(Boolean).sort().map(name => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] font-black text-[#1A2E1A] px-1 block uppercase">Church District Focus</label>
                <select 
                  value={filterChurchDistrict}
                  onChange={(e) => {setFilterChurchDistrict(e.target.value); setFilterDistrict('');}}
                  className="w-full bg-white border-2 border-[#2E7D32] rounded-lg p-4 text-xs text-[#1A2E1A] font-black outline-none focus:border-[#FFC107]"
                >
                  <option value="">All Regions</option>
                  {[...new Set(churches.map(c => c.district_name))].filter(Boolean).sort().map(name => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] font-black text-[#1A2E1A] px-1 block uppercase">Political Territory View</label>
                <select 
                  value={filterDistrict}
                  onChange={(e) => {setFilterDistrict(e.target.value); setFilterChurchDistrict('');}}
                  className="w-full bg-white border-2 border-[#2E7D32] rounded-lg p-4 text-xs text-[#1A2E1A] font-black outline-none focus:border-[#FFC107]"
                >
                  <option value="">All Sectors</option>
                  {districts.sort((a,b) => a.name.localeCompare(b.name)).map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Fixed Footer */}
        <div className="p-4 bg-white border-t-2 border-[#F0F4F0] shrink-0">
          <div className="flex items-center gap-3 p-4 bg-[#F8FAF8] rounded-xl border-2 border-[#F0F4F0]">
              <div className="w-10 h-10 rounded-lg bg-[#2E7D32] text-white flex items-center justify-center shrink-0 shadow-sm">
                <LayoutDashboard size={20} />
              </div>
              <div className="overflow-hidden">
                <p className="text-[10px] font-black text-[#2E7D32] uppercase tracking-[0.2em] leading-tight truncate">Engine v7.0</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                    <div className="w-1.5 h-1.5 bg-[#F9A825] rounded-full animate-pulse"></div>
                    <p className="text-[8px] text-[#1A2E1A]/40 font-black uppercase tracking-widest">Nominal Status</p>
                </div>
              </div>
          </div>
        </div>
      </aside>

      {/* Main Canvas - Edge to Edge */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-white">
        <header className="h-16 md:h-20 bg-[#2E7D32] flex items-center justify-between px-4 md:px-10 z-10 shrink-0 shadow-lg border-b border-white/10 gap-4">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors md:hidden"
            >
              <Menu size={24} />
            </button>
            <h2 className="text-[9px] md:text-xs font-black text-white tracking-[0.2em] md:tracking-[0.4em] uppercase truncate hidden xs:block">
              {activeTab === 'map' ? 'Institutional GIS View' : 'Mission Analytics & Reports'}
            </h2>
          </div>
          
          <div className="flex-1 flex items-center justify-end gap-3 md:gap-6 max-w-2xl">
            {/* Aesthetic Top-Bar Search Bar */}
            <div className="header-search-glass flex items-center relative h-10 md:h-11 px-3 md:px-4 flex-1 sm:max-w-xs md:max-w-md">
              <Search className="text-white/50 mr-2 md:mr-3" size={16} />
              <input 
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1"
              />
              {searchTerm && (
                <button 
                  onClick={() => setSearchTerm('')}
                  className="p-1 md:p-1.5 hover:bg-white/10 rounded-full transition-colors"
                >
                  <Trash2 className="text-white/50" size={12} />
                </button>
              )}
            </div>

            <button 
              onClick={() => setShowReportForm(true)}
              className="px-4 md:px-8 py-2.5 md:py-3.5 bg-white text-[#2E7D32] hover:bg-[#FFC107] hover:text-white rounded-lg text-[9px] md:text-[10px] font-black uppercase tracking-[0.2em] md:tracking-[0.3em] transition-all active:scale-95 shadow-xl whitespace-nowrap"
            >
              <span className="sm:inline hidden">Log Mission Activity</span>
              <span className="sm:hidden inline">Log Data</span>
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto no-scrollbar relative p-0">
            {loading ? (
                <div className="flex flex-col items-center justify-center h-full gap-4">
                    <div className="w-14 h-14 border-4 border-[#2E7D32] border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-[#2E7D32] font-black uppercase tracking-[0.4em] text-[10px] animate-pulse">Syncing Mission Intel...</p>
                </div>
            ) : (
                <AnimatePresence mode="wait">
                  {activeTab === 'map' && (
                    <motion.div 
                      key="map-tab"
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      className="h-full w-full"
                    >
                      <DistrictMap 
                        districts={filteredDistricts}
                        churches={filteredChurches}
                        selectedDistrict={selectedDistrict}
                        showBoundaries={showBoundaries}
                        onSelect={setSelectedDistrict}
                      />
                    </motion.div>
                  )}

                  {activeTab === 'reports' || activeTab === 'analytics' ? (
                    <div className="p-8">
                      <ReportsAnalytics 
                        selectedDistrict={selectedDistrict}
                        filterPastor={filterPastor}
                        churches={filteredChurches}
                      />
                    </div>
                  ) : null}
                </AnimatePresence>
            )}
        </div>
      </main>

      {/* Responsive Modal */}
      <AnimatePresence>
        {showReportForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-[#1A2E1A]/70 backdrop-blur-md" onClick={() => setShowReportForm(false)} />
            <motion.div initial={{ scale: 0.95, opacity: 0, y: 30 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0, y: 30 }} className="w-full max-w-2xl bg-white rounded-3xl relative shadow-3xl border-2 border-[#2E7D32] overflow-hidden flex flex-col max-h-[90vh]">
              <div className="p-8 sm:p-12 overflow-y-auto no-scrollbar">
                <ReportForm 
                  onClose={() => setShowReportForm(false)} 
                  pastorName={filterPastor || 'Unknown Pastor'} 
                  churches={churches}
                />
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
