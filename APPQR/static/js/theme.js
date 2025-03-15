import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#FFD700', // Color dorado para botones principales
      light: '#FFDB58', // Color mostaza para variantes más claras
      dark: '#FFB84C', // Color naranja para variantes más oscuras
      contrastText: '#212121', // Texto oscuro para contraste en botones
    },
    secondary: {
      main: '#FFB84C', // Color naranja para elementos secundarios
      light: '#FFDB58', // Color mostaza para variantes más claras
      dark: '#E09819', // Una versión más oscura del naranja
      contrastText: '#212121',
    },
    background: {
      default: '#FFF9E6', // Fondo principal color crema
      paper: '#FFFDF5', // Un tono aún más claro para tarjetas y elementos de papel
    },
    text: {
      primary: '#212121', // Casi negro para texto principal
      secondary: '#424242', // Gris oscuro para texto secundario
    },
    error: {
      main: '#FF6B6B', // Un rojo cálido que combina con la paleta
    },
    warning: {
      main: '#FFB84C', // Naranja para advertencias
    },
    info: {
      main: '#64B5F6', // Azul suave
    },
    success: {
      main: '#66BB6A', // Verde suave
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 500,
      color: '#212121',
    },
    h2: {
      fontWeight: 500,
      color: '#212121',
    },
    h3: {
      fontWeight: 500,
      color: '#212121',
    },
    h4: {
      fontWeight: 500,
      color: '#212121',
    },
    h5: {
      fontWeight: 500,
      color: '#212121',
    },
    h6: {
      fontWeight: 500,
      color: '#212121',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
          },
        },
        containedPrimary: {
          backgroundColor: '#FFD700',
          '&:hover': {
            backgroundColor: '#FFDB58',
          },
        },
        outlinedPrimary: {
          borderColor: '#FFD700',
          color: '#FFD700',
          '&:hover': {
            borderColor: '#FFDB58',
            backgroundColor: 'rgba(255, 215, 0, 0.04)',
          },
        },
        textPrimary: {
          color: '#FFD700',
          '&:hover': {
            backgroundColor: 'rgba(255, 215, 0, 0.04)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFDB58', // Barra de navegación con color mostaza
          color: '#212121', // Texto oscuro para contraste
        },
      },
    },
  },
});

export default theme; 