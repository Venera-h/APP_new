import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  Alert,
} from '@mui/material';
import { PracticalWorkCreate } from './types';

interface AddWorkDialogProps {
  open: boolean;
  onClose: () => void;
  onAdd: (work: PracticalWorkCreate) => Promise<void>;
  initialData?: PracticalWorkCreate;
  title?: string;
}

const AddWorkDialog: React.FC<AddWorkDialogProps> = ({ 
  open, 
  onClose, 
  onAdd, 
  initialData,
  title = 'Добавить практическую работу'
}) => {
  const [formData, setFormData] = useState<PracticalWorkCreate>({
    title: '',
    content: '',
    work_name: '',
    student: '',
    variant_number: 1,
    level_number: 1,
    submission_date: new Date().toISOString().split('T')[0],
    grade: 5,
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      setFormData({
        title: '',
        content: '',
        work_name: '',
        student: '',
        variant_number: 1,
        level_number: 1,
        submission_date: new Date().toISOString().split('T')[0],
        grade: 5,
      });
    }
  }, [initialData, open]);

  const handleChange = (field: keyof PracticalWorkCreate) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.type === 'number' 
      ? parseInt(event.target.value) || 0 
      : event.target.value;
    
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    // Валидация
    if (!formData.title.trim()) {
      setError('Заголовок обязателен');
      return;
    }
    if (!formData.work_name.trim()) {
      setError('Название работы обязательно');
      return;
    }
    if (!formData.student.trim()) {
      setError('ФИО студента обязательно');
      return;
    }
    if (formData.grade < 1 || formData.grade > 5) {
      setError('Оценка должна быть от 1 до 5');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await onAdd(formData);
      
      // Сброс формы
      setFormData({
        title: '',
        content: '',
        work_name: '',
        student: '',
        variant_number: 1,
        level_number: 1,
        submission_date: new Date().toISOString().split('T')[0],
        grade: 5,
      });
      
      onClose();
    } catch (err) {
      setError('Ошибка при добавлении работы');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Заголовок"
              value={formData.title}
              onChange={handleChange('title')}
              required
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Описание"
              value={formData.content}
              onChange={handleChange('content')}
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Название работы"
              value={formData.work_name}
              onChange={handleChange('work_name')}
              required
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="ФИО студента"
              value={formData.student}
              onChange={handleChange('student')}
              required
            />
          </Grid>
          
          <Grid item xs={6}>
            <TextField
              fullWidth
              type="number"
              label="Номер варианта"
              value={formData.variant_number}
              onChange={handleChange('variant_number')}
              inputProps={{ min: 1 }}
            />
          </Grid>
          
          <Grid item xs={6}>
            <TextField
              fullWidth
              type="number"
              label="Номер уровня"
              value={formData.level_number}
              onChange={handleChange('level_number')}
              inputProps={{ min: 1 }}
            />
          </Grid>
          
          <Grid item xs={6}>
            <TextField
              fullWidth
              type="date"
              label="Дата сдачи"
              value={formData.submission_date}
              onChange={handleChange('submission_date')}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          
          <Grid item xs={6}>
            <TextField
              fullWidth
              type="number"
              label="Оценка"
              value={formData.grade}
              onChange={handleChange('grade')}
              inputProps={{ min: 1, max: 5 }}
            />
          </Grid>
        </Grid>
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
          {loading ? (initialData ? 'Сохранение...' : 'Добавление...') : (initialData ? 'Сохранить' : 'Добавить')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddWorkDialog;