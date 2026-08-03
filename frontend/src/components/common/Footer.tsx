// frontend/src/components/common/Footer.tsx
import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
      <div className="container mx-auto px-4 py-4 text-center text-gray-600 dark:text-gray-300 text-sm">
        <p>
          PAPI v1.0.0 &copy; {new Date().getFullYear()}
        </p>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
          Управление активами предприятия
        </p>
      </div>
    </footer>
  );
};

export default Footer;