import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
  Tabs,
  Tab,
  Box,
} from '@mui/material';
import { User } from './types';
import { apiService } from './apiService';

interface LoginDialogProps {
  open: boolean;
  onClose: () => void;
  onLogin: () => void;
}

const LoginDialog: React.FC<LoginDialogProps> = ({ open, onClose, onLogin }) => {
  const [tab, setTab] = useState(0);
  const [formData, setFormData] = useState<User>({
    login: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (field: keyof User) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleSubmit = async () => {
    if (!formData.login.trim() || !formData.password.trim()) {
      setError('Заполните все поля');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      if (tab === 0) {
        await apiService.login(formData);
      } else {
        await apiService.register(formData);
      }
      
      setFormData({ login: '', password: '' });
      onLogin();
    } catch (err) {
      setError(tab === 0 ? 'Неверный логин или пароль' : 'Ошибка регистрации');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
    setError(null);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Tabs value={tab} onChange={handleTabChange} centered>
          <Tab label="Вход" />
          <Tab label="Регистрация" />
        </Tabs>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Box sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="Логин"
            value={formData.login}
            onChange={handleChange('login')}
            margin="normal"
            required
          />
          
          <TextField
            fullWidth
            type="password"
            label="Пароль"
            value={formData.password}
            onChange={handleChange('password')}
            margin="normal"
            required
          />
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Отмена
        </Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          disabled={loading}
        >
          {loading ? 'Загрузка...' : (tab === 0 ? 'Войти' : 'Зарегистрироваться')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default LoginDialog;