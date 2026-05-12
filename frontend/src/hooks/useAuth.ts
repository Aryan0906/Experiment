/**
 * Convenience hook for accessing authentication context
 */
import { useAuth as useAuthContext } from '../context/AuthContext';

export const useAuth = () => {
    return useAuthContext();
};

export default useAuth;
