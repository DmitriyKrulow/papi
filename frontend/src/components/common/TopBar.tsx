// frontend/src/components/common/TopBar.tsx
import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';
import { useNavSections } from '../navigation/navItems';
import { Sun, Moon, UserCog, LogOut, Menu, X, Bell, Search, X as XIcon } from 'lucide-react';
import NotificationDropdown from '../notifications/NotificationDropdown';

interface SearchResult {
  id: number;
  inventory_number: string;
  name: string;
  asset_type?: string;
  location_address?: string;
  responsible_person?: string;
}

const TopBar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAuthenticated, isAdmin } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Состояния для поиска
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchDropdownRef = useRef<HTMLDivElement>(null);

  const navSections = useNavSections(isAdmin);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileMenuOpen(false);
  };

  // Загрузка результатов поиска с debounce
  const performSearch = useCallback(async (query: string) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      setSearchLoading(false);
      return;
    }

    setSearchLoading(true);
    try {
      const token = localStorage.getItem('token');
      const url = `/api/assets/?search=${encodeURIComponent(query)}&limit=20&include_hidden=false`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        console.error(`[TopBar Search] HTTP error: ${response.status} ${response.statusText}`);
        if (response.status === 401 || response.status === 403) {
          console.error('[TopBar Search] Unauthorized — возможно, сессия истекла');
        }
        setSearchResults([]);
      } else {
        const data = await response.json();
        const items = data.items || [];
        setSearchResults(items);
        console.log(`[TopBar Search] Found ${items.length} results for "${query}"`);
      }
    } catch (error) {
      console.error('[TopBar Search] Fetch error:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }, []);

  // Debounce для поиска
  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);

    if (searchTerm.length >= 2) {
      searchTimerRef.current = setTimeout(() => {
        performSearch(searchTerm);
      }, 300);
    } else {
      setSearchResults([]);
      setSearchLoading(false);
    }

    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    };
  }, [searchTerm, performSearch]);

  // Закрытие dropdown при клике вне его
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchDropdownRef.current && !searchDropdownRef.current.contains(event.target as Node)) {
        setSearchOpen(false);
      }
    };

    if (searchOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [searchOpen]);

  // Закрытие dropdown при смене маршрута
  useEffect(() => {
    setSearchOpen(false);
    setSearchTerm('');
    setSearchResults([]);
  }, [location.pathname]);

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    if (value.length >= 2 && !searchOpen) {
      setSearchOpen(true);
    }
    if (value.length < 2) {
      setSearchOpen(false);
    }
  };

  const handleSelectResult = (assetId: number) => {
    setSearchOpen(false);
    setSearchTerm('');
    setSearchResults([]);
    navigate(`/assets/${assetId}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchResults.length > 0) {
      handleSelectResult(searchResults[0].id);
    }
    if (e.key === 'Escape') {
      setSearchOpen(false);
    }
  };

  const getAssetTypeIcon = (assetType?: string) => {
    const icons: Record<string, string> = {
      furniture: '🪑',
      computer: '💻',
      printer: '🖨️',
      multifunction: '🖥️',
      it_network: '🖧',
      fire_extinguisher: '🧯',
      security: '🛡️',
      ventilation: '❄️',
      electrical: '⚡',
      power_supply: '🔋',
      plumbing: '🚿',
      doors_windows: '🚪',
      tools: '🔧',
      appliances: '🔌',
      parking: '🅿️',
      communication: '📞',
      consumables: '📦',
      ppe: '🦺',
      other: '📦',
    };
    return icons[assetType || ''] || '📦';
  };

  return (
    <header className="sticky top-0 z-20 bg-white/80 dark:bg-graphite-900/80 backdrop-blur-md border-b border-gray-100 dark:border-graphite-800">
      <div className="flex items-center justify-between h-12 px-4">
        {/* Left: Logo */}
        <Link to="/dashboard" className="flex items-center gap-2 flex-shrink-0">
          <span className="text-lg">🏗️</span>
          <span className="hidden sm:block font-bold text-brand-600 dark:text-accent-400 text-sm">PAPI</span>
        </Link>

        {/* Center: Search (desktop) */}
        <div className="hidden md:flex flex-1 max-w-md mx-4 relative" ref={searchDropdownRef}>
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск активов, помещений..."
              value={searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => { if (searchResults.length > 0) setSearchOpen(true); }}
              className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-200 dark:border-graphite-700 rounded-lg bg-gray-50 dark:bg-graphite-800 text-gray-900 dark:text-graphite-100 focus:outline-none focus:ring-1 focus:ring-accent-400/50 transition-all placeholder:text-gray-400"
            />
            {searchTerm && (
              <button
                onClick={() => { setSearchTerm(''); setSearchResults([]); setSearchOpen(false); }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XIcon className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Search results dropdown — position fixed to avoid z-index issues */}
          {searchOpen && (
            <div 
              className="fixed left-0 right-0 bg-white dark:bg-graphite-800 border border-gray-200 dark:border-graphite-700 rounded-lg shadow-xl max-h-80 overflow-y-auto z-[100] mt-12"
              style={{ top: '0px' }}
            >
              <div className="max-w-md mx-auto px-4">
                {searchLoading ? (
                  <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
                    Поиск...
                  </div>
                ) : searchResults.length > 0 ? (
                  <div className="py-1">
                    {searchResults.map((asset) => (
                      <button
                        key={asset.id}
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleSelectResult(asset.id);
                        }}
                        className="w-full px-4 py-2.5 text-left hover:bg-gray-50 dark:hover:bg-graphite-700 transition flex items-center gap-3"
                      >
                        <span className="text-lg flex-shrink-0">{getAssetTypeIcon(asset.asset_type)}</span>
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                            {asset.name}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                            {asset.inventory_number}
                            {asset.responsible_person && ` • ${asset.responsible_person}`}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : searchTerm.length >= 2 ? (
                  <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
                    Ничего не найдено
                  </div>
                ) : null}
              </div>
            </div>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1">
          {isAuthenticated && <NotificationDropdown />}

          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-graphite-800 transition-colors"
            title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-yellow-500" />
            ) : (
              <Moon className="w-4 h-4 text-gray-500" />
            )}
          </button>

          {isAuthenticated && user && (
            <Link 
              to="/profile" 
              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-graphite-800 transition-colors"
              title={user.username}
            >
              <UserCog className="w-4 h-4 text-brand-500 dark:text-accent-400" />
            </Link>
          )}

          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Выйти"
            >
              <LogOut className="w-4 h-4 text-gray-400 hover:text-red-500 transition-colors" />
            </button>
          )}

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-graphite-800 transition-colors"
          >
            {mobileMenuOpen ? (
              <X className="w-5 h-5 text-gray-500" />
            ) : (
              <Menu className="w-5 h-5 text-gray-500" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-gray-100 dark:border-graphite-800 bg-white dark:bg-graphite-900 py-2 px-3 space-y-4 max-h-[80vh] overflow-y-auto">
          {/* Search (mobile) */}
          <div className="md:hidden">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск..."
                value={searchTerm}
                onChange={(e) => handleSearchChange(e.target.value)}
                onKeyDown={handleKeyDown}
                className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-accent-400/50 placeholder:text-gray-400"
              />
            </div>
          </div>
          
          {/* User info */}
          {isAuthenticated && user && (
            <div className="px-2 py-1.5 text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <UserCog className="w-4 h-4" />
              {user.username}
            </div>
          )}
          
          {/* Navigation sections */}
          {isAuthenticated && (
            <>
              {navSections.map(section => (
                <div key={section.title}>
                  <div className="px-2 py-1 text-xs font-semibold text-gray-400 dark:text-gray-600 uppercase tracking-wider">
                    {section.title}
                  </div>
                  <div className="space-y-0.5">
                    {section.items.map(item => (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => setMobileMenuOpen(false)}
                        className="block px-3 py-2 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-700 dark:text-gray-300 flex items-center gap-2"
                      >
                        <span className="flex-shrink-0">{item.icon}</span>
                        <span>{item.label}</span>
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Logout */}
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-red-500 flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Выйти
            </button>
          )}
        </div>
      )}
    </header>
  );
};

export default TopBar;
