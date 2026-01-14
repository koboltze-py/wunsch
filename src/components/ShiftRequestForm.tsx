'use client';

import React, { useState, useEffect } from 'react';
import { ShiftRequest, ShiftType } from '../types/shift';
import { createShiftRequest, getUserShiftRequests } from '../actions/shift-request';

interface SubmittedRequest {
  id: string;
  date: Date;
  shiftType: string;
  remarks: string | null;
  status: string;
  createdAt: Date;
}

const ShiftRequestForm: React.FC = () => {
  const [formData, setFormData] = useState<ShiftRequest>({
    date: null,
    shiftType: '',
    remarks: ''
  });

  const [errors, setErrors] = useState<{
    date?: string;
    shiftType?: string;
  }>({});

  const [isLoading, setIsLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [submittedRequests, setSubmittedRequests] = useState<SubmittedRequest[]>([]);
  const [isLoadingRequests, setIsLoadingRequests] = useState(true);

  const shiftTypes: ShiftType[] = ['Früh', 'Spät', 'Nacht'];

  // Lade bereits abgegebene Wünsche für den aktuellen Monat
  useEffect(() => {
    loadSubmittedRequests();
  }, []);

  const loadSubmittedRequests = async () => {
    setIsLoadingRequests(true);
    try {
      const result = await getUserShiftRequests();
      if (result.success && result.data) {
        // Filtere nur Wünsche des aktuellen Monats
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();
        
        const currentMonthRequests = (result.data as SubmittedRequest[]).filter(request => {
          const requestDate = new Date(request.date);
          return requestDate.getMonth() === currentMonth && 
                 requestDate.getFullYear() === currentYear;
        });
        
        setSubmittedRequests(currentMonthRequests);
      }
    } catch (error) {
      console.error('Fehler beim Laden der Dienstwünsche:', error);
    } finally {
      setIsLoadingRequests(false);
    }
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const dateValue = e.target.value ? new Date(e.target.value) : null;
    
    // Validierung: Datum darf nicht in der Vergangenheit liegen
    if (dateValue) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      dateValue.setHours(0, 0, 0, 0);
      
      if (dateValue < today) {
        setErrors(prev => ({ 
          ...prev, 
          date: 'Das Datum darf nicht in der Vergangenheit liegen' 
        }));
        return;
      }
    }
    
    setFormData(prev => ({ ...prev, date: dateValue }));
    if (errors.date) {
      setErrors(prev => ({ ...prev, date: undefined }));
    }
  };

  const handleShiftTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, shiftType: e.target.value as ShiftType | '' }));
    if (errors.shiftType) {
      setErrors(prev => ({ ...prev, shiftType: undefined }));
    }
  };

  const handleRemarksChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, remarks: e.target.value }));
  };

  const validateForm = (): boolean => {
    const newErrors: { date?: string; shiftType?: string } = {};

    if (!formData.date) {
      newErrors.date = 'Bitte wählen Sie ein Datum aus';
    } else {
      // Zusätzliche Validierung: Datum nicht in der Vergangenheit
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const selectedDate = new Date(formData.date);
      selectedDate.setHours(0, 0, 0, 0);
      
      if (selectedDate < today) {
        newErrors.date = 'Das Datum darf nicht in der Vergangenheit liegen';
      }
    }

    if (!formData.shiftType) {
      newErrors.shiftType = 'Bitte wählen Sie eine Schichtart aus';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setShowSuccess(false);
    
    try {
      const result = await createShiftRequest({
        date: formData.date!,
        shiftType: formData.shiftType as ShiftType,
        remarks: formData.remarks || null,
      });

      if (result.success) {
        // Erfolgsmeldung anzeigen
        setShowSuccess(true);
        
        // Formular zurücksetzen
        setFormData({
          date: null,
          shiftType: '',
          remarks: ''
        });
        
        // Liste aktualisieren
        await loadSubmittedRequests();
        
        // Erfolgsmeldung nach 5 Sekunden ausblenden
        setTimeout(() => {
          setShowSuccess(false);
        }, 5000);
      } else {
        // Fehler anzeigen
        if (result.fieldErrors) {
          setErrors({
            date: result.fieldErrors.date?.[0],
            shiftType: result.fieldErrors.shiftType?.[0],
          });
        } else {
          alert(result.error || 'Ein Fehler ist aufgetreten');
        }
      }
    } catch (error) {
      console.error('Fehler beim Einreichen:', error);
      alert('Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDateForInput = (date: Date | null): string => {
    if (!date) return '';
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const formatDateForDisplay = (date: Date): string => {
    return new Date(date).toLocaleDateString('de-DE', {
      weekday: 'short',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getStatusBadgeColor = (status: string): string => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'APPROVED':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'REJECTED':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'PENDING':
        return 'Ausstehend';
      case 'APPROVED':
        return 'Genehmigt';
      case 'REJECTED':
        return 'Abgelehnt';
      default:
        return status;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-red-600 rounded-full mb-4">
            <svg 
              className="w-8 h-8 text-white" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" 
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Dienstwunsch
          </h1>
          <p className="text-gray-600">
            Teilen Sie uns Ihren Schichtwunsch mit
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 mb-6">
          {/* Erfolgsmeldung */}
          {showSuccess && (
            <div className="mb-6 p-4 bg-green-50 border-2 border-green-200 rounded-lg flex items-start animate-fade-in">
              <svg className="w-6 h-6 text-green-600 mr-3 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="text-sm font-semibold text-green-800 mb-1">
                  Erfolgreich eingereicht!
                </h3>
                <p className="text-sm text-green-700">
                  Ihr Dienstwunsch wurde erfolgreich übermittelt und wird bearbeitet.
                </p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Datum Field */}
            <div>
              <label 
                htmlFor="date" 
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Datum <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                id="date"
                value={formatDateForInput(formData.date)}
                onChange={handleDateChange}
                className={`w-full px-4 py-3 rounded-lg border-2 transition-colors duration-200 
                  ${errors.date 
                    ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                    : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
                  } 
                  focus:outline-none focus:ring-2 focus:ring-opacity-50 text-gray-900`}
                min={new Date().toISOString().split('T')[0]}
              />
              {errors.date && (
                <p className="mt-2 text-sm text-red-600 flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {errors.date}
                </p>
              )}
            </div>

            {/* Schichtart Dropdown */}
            <div>
              <label 
                htmlFor="shiftType" 
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Schichtart <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <select
                  id="shiftType"
                  value={formData.shiftType}
                  onChange={handleShiftTypeChange}
                  className={`w-full px-4 py-3 rounded-lg border-2 transition-colors duration-200 
                    ${errors.shiftType 
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                      : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
                    } 
                    focus:outline-none focus:ring-2 focus:ring-opacity-50 text-gray-900 
                    appearance-none bg-white cursor-pointer`}
                >
                  <option value="">Bitte wählen...</option>
                  {shiftTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-gray-600">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              {errors.shiftType && (
                <p className="mt-2 text-sm text-red-600 flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {errors.shiftType}
                </p>
              )}
            </div>

            {/* Bemerkungen Textarea */}
            <div>
              <label 
                htmlFor="remarks" 
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Bemerkungen
              </label>
              <textarea
                id="remarks"
                value={formData.remarks}
                onChange={handleRemarksChange}
                rows={4}
                placeholder="Optional: Fügen Sie hier weitere Informationen hinzu..."
                className="w-full px-4 py-3 rounded-lg border-2 border-gray-300 
                  focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50 
                  focus:outline-none transition-colors duration-200 text-gray-900 
                  placeholder-gray-400 resize-none"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-indigo-600 to-indigo-700 
                hover:from-indigo-700 hover:to-indigo-800 
                text-white font-semibold py-3.5 px-6 rounded-lg 
                transition-all duration-200 transform hover:scale-[1.02] 
                focus:outline-none focus:ring-4 focus:ring-indigo-500 focus:ring-opacity-50 
                shadow-lg hover:shadow-xl active:scale-[0.98]
                disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
                flex items-center justify-center"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Wird gesendet...
                </>
              ) : (
                'Dienstwunsch einreichen'
              )}
            </button>
          </form>
        </div>

        {/* Footer Info */}
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>* Pflichtfelder</p>
        </div>

        {/* Übersicht bereits abgegebener Wünsche */}
        <div className="mt-8 bg-white rounded-2xl shadow-xl p-6 sm:p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center">
              <svg className="w-6 h-6 mr-2 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Meine Wünsche diesen Monat
            </h2>
            <span className="text-sm text-gray-500">
              {new Date().toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })}
            </span>
          </div>

          {isLoadingRequests ? (
            <div className="flex items-center justify-center py-12">
              <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="ml-3 text-gray-600">Lade Dienstwünsche...</span>
            </div>
          ) : submittedRequests.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              <p className="text-gray-500 text-lg font-medium mb-2">
                Noch keine Wünsche eingereicht
              </p>
              <p className="text-gray-400 text-sm">
                Sie haben noch keine Dienstwünsche für diesen Monat abgegeben.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {submittedRequests.map((request) => (
                <div 
                  key={request.id} 
                  className="border-2 border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors duration-200"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <svg className="w-5 h-5 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <span className="font-semibold text-gray-900">
                          {formatDateForDisplay(request.date)}
                        </span>
                      </div>
                      
                      <div className="flex items-center mb-2">
                        <svg className="w-5 h-5 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-gray-700 font-medium">
                          {request.shiftType}
                        </span>
                      </div>
                      
                      {request.remarks && (
                        <div className="flex items-start mt-2">
                          <svg className="w-5 h-5 text-gray-400 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                          </svg>
                          <span className="text-sm text-gray-600">
                            {request.remarks}
                          </span>
                        </div>
                      )}
                    </div>
                    
                    <div>
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadgeColor(request.status)}`}>
                        {getStatusText(request.status)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ShiftRequestForm;
