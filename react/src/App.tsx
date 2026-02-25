import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  Alert,
  AppBar,
  Toolbar,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Add, Edit, Delete, ExitToApp, Search, Clear, Sort } from '@mui/icons-material';
import { PracticalWorkOut, PracticalWorkCreate } from './types';
import { apiService } from './apiService';
import AddWorkDialog from './AddWorkDialog';
import LoginDialog from './LoginDialog';

const App: React.FC = () => {
  const [works, setWorks] = useState<PracticalWorkOut[]>([]);
  const [filteredWorks, setFilteredWorks] = useState<PracticalWorkOut[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingWork, setEditingWork] = useState<PracticalWorkOut | null>(null);
  const [loginDialogOpen, setLoginDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setIsAuthenticated(apiService.isAuthenticated());
    if (apiService.isAuthenticated()) {
      loadWorks();
    }
  }, []);

  useEffect(() => {
    let filtered = works;
    
    if (searchQuery.trim()) {
      filtered = works.filter(work => 
        work.student.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Сортировка по дате
    filtered = [...filtered].sort((a, b) => {
      const dateA = new Date(a.submission_date).getTime();
      const dateB = new Date(b.submission_date).getTime();
      return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
    });
    
    setFilteredWorks(filtered);
  }, [works, searchQuery, sortOrder]);

  const loadWorks = async () => {
    try {
      setLoading(true);
      const worksData = await apiService.getWorks();
      setWorks(worksData);
      setFilteredWorks(worksData);
    } catch (err) {
      setError('Ошибка загрузки работ');
    } finally {
      setLoading(false);
    }
  };

  const handleAddWork = async (work: PracticalWorkCreate) => {
    try {
      const newWork = await apiService.createWork(work);
      setWorks(prev => [...prev, newWork]);
    } catch (err) {
      throw new Error('Ошибка создания работы');
    }
  };

  const handleEditWork = async (work: PracticalWorkCreate) => {
    if (!editingWork) return;
    try {
      const updatedWork = await apiService.updateWork(editingWork.id, work);
      setWorks(prev => prev.map(w => w.id === editingWork.id ? updatedWork : w));
      setEditDialogOpen(false);
      setEditingWork(null);
    } catch (err) {
      throw new Error('Ошибка обновления работы');
    }
  };

  const openEditDialog = (work: PracticalWorkOut) => {
    setEditingWork(work);
    setEditDialogOpen(true);
  };

  const handleDeleteWork = async (id: number) => {
    try {
      await apiService.deleteWork(id);
      setWorks(prev => prev.filter(work => work.id !== id));
    } catch (err) {
      setError('Ошибка удаления работы');
    }
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
    setLoginDialogOpen(false);
    loadWorks();
  };

  const handleLogout = () => {
    apiService.logout();
    setIsAuthenticated(false);
    setWorks([]);
  };

  if (!isAuthenticated) {
    return (
      <Container maxWidth="sm" sx={{ mt: 8 }}>
        <Card>
          <CardContent sx={{ textAlign: 'center', p: 4 }}>
            <Typography variant="h4" gutterBottom>
              База данных практических работ
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Войдите в систему для управления практическими работами
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => setLoginDialogOpen(true)}
            >
              Войти
            </Button>
          </CardContent>
        </Card>
        
        <LoginDialog
          open={loginDialogOpen}
          onClose={() => setLoginDialogOpen(false)}
          onLogin={handleLogin}
        />
      </Container>
    );
  }

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            База данных практических работ
          </Typography>
          <Button
            color="inherit"
            startIcon={<Add />}
            onClick={() => setAddDialogOpen(true)}
          >
            Добавить работу
          </Button>
          <IconButton color="inherit" onClick={handleLogout}>
            <ExitToApp />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            fullWidth
            placeholder="Поиск по студенту..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
              endAdornment: searchQuery && (
                <InputAdornment position="end">
                  <IconButton onClick={() => setSearchQuery('')} size="small">
                    <Clear />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Сортировка по дате</InputLabel>
            <Select
              value={sortOrder}
              label="Сортировка по дате"
              onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
              startAdornment={<Sort sx={{ mr: 1, color: 'action.active' }} />}
            >
              <MenuItem value="desc">Новые первые</MenuItem>
              <MenuItem value="asc">Старые первые</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Typography>Загрузка...</Typography>
        ) : (
          <Grid container spacing={3}>
            {filteredWorks.map((work) => (
              <Grid item xs={12} md={6} lg={4} key={work.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6" component="h2">
                        {work.title}
                      </Typography>
                      <Box>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => openEditDialog(work)}
                          sx={{ mr: 1 }}
                        >
                          <Edit />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteWork(work.id)}
                        >
                          <Delete />
                        </IconButton>
                      </Box>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {work.content}
                    </Typography>
                    
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      <strong>Работа:</strong> {work.work_name}
                    </Typography>
                    
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Студент:</strong> {work.student}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                      <Chip label={`Вариант ${work.variant_number}`} size="small" />
                      <Chip label={`Уровень ${work.level_number}`} size="small" />
                      <Chip 
                        label={`Оценка ${work.grade}`} 
                        size="small" 
                        color={work.grade >= 4 ? 'success' : work.grade >= 3 ? 'warning' : 'error'}
                      />
                    </Box>
                    
                    <Typography variant="caption" color="text.secondary">
                      Дата сдачи: {new Date(work.submission_date).toLocaleDateString('ru-RU')}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {works.length === 0 && !loading && (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <Typography variant="h6" color="text.secondary">
              Нет практических работ
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Добавьте первую практическую работу
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setAddDialogOpen(true)}
            >
              Добавить работу
            </Button>
          </Box>
        )}

        {filteredWorks.length === 0 && works.length > 0 && !loading && (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <Typography variant="h6" color="text.secondary">
              Ничего не найдено
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Попробуйте изменить запрос поиска
            </Typography>
          </Box>
        )}
      </Container>

      <AddWorkDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        onAdd={handleAddWork}
      />

      <AddWorkDialog
        open={editDialogOpen}
        onClose={() => {
          setEditDialogOpen(false);
          setEditingWork(null);
        }}
        onAdd={handleEditWork}
        initialData={editingWork ? {
          title: editingWork.title,
          content: editingWork.content,
          work_name: editingWork.work_name,
          student: editingWork.student,
          variant_number: editingWork.variant_number,
          level_number: editingWork.level_number,
          submission_date: editingWork.submission_date,
          grade: editingWork.grade
        } : undefined}
        title={editingWork ? 'Редактировать работу' : 'Добавить работу'}
      />
    </Box>
  );
};

export default App;
                  