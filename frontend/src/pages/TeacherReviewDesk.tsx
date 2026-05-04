import React from 'react';
import QueueDesk from '@/components/QueueDesk';

const TeacherReviewDesk = () => {
  return (
    <QueueDesk 
      title="Révision Enseignants"
      endpoint="/students/queues/teacher-review"
      actionLabel="Finaliser Révision"
      actionType="RESOLVE_REVIEW"
      emptyMessage="Tous les dossiers 57-59% ont été révisés"
    />
  );
};

export default TeacherReviewDesk;
