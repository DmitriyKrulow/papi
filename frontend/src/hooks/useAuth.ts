import { useCallback } from 'react';
import { useAuthContext } from '../context/AuthContext';

export const useAuth = () => {
  return useAuthContext();
};
