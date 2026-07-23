// frontend/src/pages/Home.tsx
import { Link } from 'react-router-dom';

const Home: React.FC = () => {
  return (
    <div className="text-center py-12">
      <h1 className="text-4xl font-bold text-gray-800 mb-4">
        🏗️ PAPI - Управление активами
      </h1>
      <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
        Система для управления основными средствами и активами предприятия
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition card-hover">
          <div className="text-4xl mb-3">📦</div>
          <h3 className="text-lg font-semibold mb-2">Активы</h3>
          <p className="text-gray-600 text-sm mb-3">
            Управление основными средствами
          </p>
          <Link
            to="/assets"
            className="inline-block text-blue-600 hover:text-blue-800 font-medium"
          >
            Перейти →
          </Link>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition card-hover">
          <div className="text-4xl mb-3">🔧</div>
          <h3 className="text-lg font-semibold mb-2">Ремонты</h3>
          <p className="text-gray-600 text-sm mb-3">
            Заявки и обслуживание
          </p>
          <span className="inline-block text-gray-400 font-medium">
            В разработке →
          </span>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition card-hover">
          <div className="text-4xl mb-3">📊</div>
          <h3 className="text-lg font-semibold mb-2">Отчеты</h3>
          <p className="text-gray-600 text-sm mb-3">
            Аналитика и отчетность
          </p>
          <span className="inline-block text-gray-400 font-medium">
            В разработке →
          </span>
        </div>
      </div>
      
      <div className="mt-8">
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition inline-block"
        >
          📚 Документация API
        </a>
      </div>
    </div>
  );
};

export default Home;