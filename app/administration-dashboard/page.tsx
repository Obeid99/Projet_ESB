"use client";
import { Box, Text, Flex, Button, Image } from "@chakra-ui/react";
import { IoArrowBack, IoBarChart, IoChatbubbles, IoDownload } from 'react-icons/io5';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import axios from 'axios';

// Chart.js registration for required elements/scales
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

// Dynamically import chart.js components to avoid SSR issues
const Bar = dynamic(() => import('react-chartjs-2').then(mod => mod.Bar), { ssr: false });
const Pie = dynamic(() => import('react-chartjs-2').then(mod => mod.Pie), { ssr: false });

export default function AdministrationDashboardPage() {
  const router = useRouter();
  const [feedbackData, setFeedbackData] = useState<{ positive: number; negative: number } | null>(null);

  useEffect(() => {
    axios.get('http://127.0.0.1:5000/admin/feedback_chart', { withCredentials: true })
      .then(res => {
        // Expecting backend to return JSON: { positive: 10, negative: 5 }
        if (res.data && typeof res.data === 'object' && 'positive' in res.data && 'negative' in res.data) {
          setFeedbackData(res.data);
        }
      })
      .catch(() => {
        // fallback to demo data if backend fails
        setFeedbackData({ positive: 10, negative: 5 });
      });
  }, []);

  // Example data for charts
  const barData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Student Requests',
        data: [12, 19, 3, 5, 2, 3],
        backgroundColor: 'rgba(133, 3, 3, 0.7)',
      },
    ],
  };

  const pieData = feedbackData
    ? {
        labels: ['Positive', 'Negative'],
        datasets: [
          {
            data: [feedbackData.positive, feedbackData.negative],
            backgroundColor: [
              'rgba(72, 137, 180, 0.7)',
              'rgba(133, 3, 3, 0.7)'
            ],
          },
        ],
      }
    : {
        labels: ['Positive', 'Negative'],
        datasets: [
          {
            data: [10, 5],
            backgroundColor: [
              'rgba(72, 137, 180, 0.7)',
              'rgba(133, 3, 3, 0.7)'
            ],
          },
        ],
      };

  return (
    <Flex w="100vw" h="100vh">
      {/* Sidebar */}
      <Flex
        direction="column"
        w="250px"
        bg="red.500"
        color="white"
        p="20px"
        justifyContent="flex-start"
        alignItems="center"
      >
        <Box mb="9" display="flex" flexDirection="column" alignItems="center" w="100%">
          <Image
            src="/img/esb.png"
            boxSize="120px"
            borderRadius="full"
            mb="4"
            border="3px solid white"
          />
        </Box>
        <Button
          leftIcon={<IoArrowBack size={20} color="#e53e3e" />}
          variant="solid"
          bg="white"
          color="red.500"
          _hover={{ bg: 'red.100' }}
          _active={{ bg: 'red.200' }}
          w="full"
          mb="10px"
          onClick={() => router.push('/welcome')}
        >
          Back
        </Button>
        <Button
          leftIcon={<IoBarChart size={20} color="#e53e3e" />}
          variant="solid"
          bg="white"
          color="red.500"
          _hover={{ bg: 'red.100' }}
          _active={{ bg: 'red.200' }}
          w="full"
          mb="10px"
          onClick={() => router.push('/administration-dashboard')}
        >
          Dashboard
        </Button>
        <Button
          leftIcon={<IoChatbubbles size={20} color="#e53e3e" />}
          variant="solid"
          bg="white"
          color="red.500"
          _hover={{ bg: 'red.100' }}
          _active={{ bg: 'red.200' }}
          w="full"
          mb="10px"
          onClick={() => router.push('/administration-chatbot')}
        >
          Chatbot
        </Button>
        
      </Flex>

      {/* Dashboard Content */}
      <Flex flex="1" direction="column" alignItems="center" justifyContent="flex-start" bg="gray.100" p="40px" gap={10}>
        <Box w="100%" maxW="1000px" bg="white" borderRadius="md" boxShadow="md" p="40px" textAlign="center" mb={10}>
          <Text fontSize="2xl" fontWeight="bold" mb="10px" color="red.500">
            Administration Dashboard
          </Text>
          <Text fontSize="lg" mb="20px" color="gray.700">
            Overview of Student Requests and Status
          </Text>
        </Box>
        <Flex w="100%" maxW="1000px" gap={10} direction={{ base: 'column', md: 'row' }}>
          <Box flex={1} bg="white" borderRadius="md" boxShadow="md" p="40px" textAlign="center">
            <Text fontWeight="bold" mb="4" fontSize="xl">Requests per Month</Text>
            <Box w="100%" h="400px">
              <Bar data={barData} options={{ maintainAspectRatio: false }} height={400} />
            </Box>
          </Box>
          <Box flex={1} bg="white" borderRadius="md" boxShadow="md" p="40px" textAlign="center">
            <Text fontWeight="bold" mb="4" fontSize="xl">Feedback Chart</Text>
            <Box w="100%" h="400px">
              <Pie data={pieData} options={{ maintainAspectRatio: false }} height={400} />
            </Box>
          </Box>
        </Flex>
      </Flex>
    </Flex>
  );
}
